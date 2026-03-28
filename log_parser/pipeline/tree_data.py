from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

LEVEL_COLORS = {
    "INFO": "blue",
    "WARN": "orange",
    "ERROR": "red",
}


def _event_from_text(text: str, fallback: str) -> str:
    low = text.lower()
    if any(k in low for k in ["login", "logged in", "logout", "auth", "token"]):
        return "login"
    if any(k in low for k in ["database", "db", "query", "transaction"]):
        return "database"
    if any(k in low for k in ["request", "http", "endpoint", "api"]):
        return "request"
    if any(k in low for k in ["timeout", "timed out", "latency"]):
        return "timeout"
    if fallback and fallback.upper() != "GENERIC":
        return fallback.lower()
    return "generic"


def build_template_tree(
    trace: dict[str, Any],
    template_stats: list[dict[str, Any]],
    show_current_batch: bool = True,
    debug_mode: bool = False,
    instance_limit: int = 25,
) -> dict[str, Any]:
    stat_map = {item["template_text"]: item for item in template_stats}
    levels: dict[str, dict[str, Any]] = defaultdict(lambda: {"event_types": defaultdict(dict)})

    batches = trace.get("batches", [])
    latest_batch_id = max((b.get("batch_id", 0) for b in batches), default=0)

    template_index: dict[tuple[str, str, str], dict[str, Any]] = {}

    for batch in batches:
        batch_id = int(batch.get("batch_id", 0))
        cluster_id = str(batch.get("cluster_id", ""))
        slm_raw_output = str(batch.get("slm_raw_output", ""))

        for item in batch.get("logs", []):
            level = str(item.get("level", "INFO")).upper()
            level = level if level in LEVEL_COLORS else "INFO"
            event = _event_from_text(str(item.get("text", "")), str(item.get("event_type", "")))
            template = str(item.get("template", ""))
            source = str(item.get("source", "SLM")).upper()

            key = (level, event, template)
            if key not in template_index:
                stats = stat_map.get(template, {})
                template_index[key] = {
                    "template_text": template,
                    "count": 0,
                    "global_count": int(stats.get("usage_count", 0)),
                    "first_seen": str(stats.get("first_seen", "")),
                    "last_seen": str(stats.get("last_used", "")),
                    "source": {"cache": 0, "slm": 0},
                    "current_batch_count": 0,
                    "highlight_current_batch": False,
                    "instances": [],
                    "instances_total": 0,
                    "instances_truncated": False,
                    "omitted_instances": 0,
                    "example_logs": [],
                    "debug": {
                        "cluster_ids": set(),
                        "cache_hit": 0,
                        "cache_miss": 0,
                        "raw_slm_outputs": set(),
                    },
                }

            node = template_index[key]
            node["count"] += 1
            if source == "CACHE":
                node["source"]["cache"] += 1
                node["debug"]["cache_hit"] += 1
            else:
                node["source"]["slm"] += 1
                node["debug"]["cache_miss"] += 1

            in_current_batch = batch_id == latest_batch_id
            if in_current_batch:
                node["current_batch_count"] += 1
                node["highlight_current_batch"] = True

            node["instances_total"] += 1
            if len(node["instances"]) < instance_limit:
                node["instances"].append(
                    {
                        "original_log": str(item.get("text", "")),
                        "source": source,
                        "batch_id": batch_id,
                        "cluster_id": cluster_id,
                        "masked": str(item.get("masked", "")),
                        "in_current_batch": in_current_batch,
                    }
                )
            else:
                node["instances_truncated"] = True
                node["omitted_instances"] += 1

            log_text = str(item.get("text", ""))
            if log_text and log_text not in node["example_logs"] and len(node["example_logs"]) < 3:
                node["example_logs"].append(log_text)

            node["debug"]["cluster_ids"].add(cluster_id)
            if slm_raw_output:
                node["debug"]["raw_slm_outputs"].add(slm_raw_output)

    for (level, event, template), node in template_index.items():
        total = max(node["count"], 1)
        node["source"]["cache_pct"] = round((node["source"]["cache"] / total) * 100.0, 2)
        node["source"]["slm_pct"] = round((node["source"]["slm"] / total) * 100.0, 2)

        if not show_current_batch:
            node["highlight_current_batch"] = False
            node["current_batch_count"] = 0

        if not debug_mode:
            node.pop("debug", None)
        else:
            node["debug"]["cluster_ids"] = sorted(node["debug"]["cluster_ids"])
            node["debug"]["raw_slm_outputs"] = list(node["debug"]["raw_slm_outputs"])[:3]

        event_bucket = levels[level]["event_types"].setdefault(event, {"templates": []})
        event_bucket["templates"].append(node)

    result_levels: dict[str, Any] = {}
    for level, payload in levels.items():
        event_types = payload["event_types"]
        for event_name, event_payload in event_types.items():
            event_payload["templates"].sort(key=lambda x: x["count"], reverse=True)
        result_levels[level] = {
            "color": LEVEL_COLORS[level],
            "event_types": dict(sorted(event_types.items(), key=lambda kv: kv[0])),
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_batch_id": latest_batch_id,
        "show_current_batch": show_current_batch,
        "debug_mode": debug_mode,
        "total_logs": int(trace.get("total_logs", 0)),
        "levels": dict(sorted(result_levels.items(), key=lambda kv: kv[0])),
    }
