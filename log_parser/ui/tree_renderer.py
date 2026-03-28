from __future__ import annotations

import html
from typing import Any

_LEVEL_COLORS = {
    "INFO": "#1d4ed8",
    "WARN": "#c2410c",
    "ERROR": "#b91c1c",
}


def _source_badge(source: str) -> str:
    src = source.upper()
    color = "#16a34a" if src == "CACHE" else "#7e22ce"
    return f"<span class='src-badge' style='background:{color};'>{html.escape(src)}</span>"


def render_tree_html(tree: dict[str, Any], show_current_batch: bool, debug_mode: bool) -> str:
    levels = tree.get("levels", {})
    latest_batch_id = tree.get("latest_batch_id", 0)

    parts: list[str] = [
        "<style>",
        ".tree-wrap{font-family:Segoe UI,Arial,sans-serif;background:#f8fafc;padding:14px;border-radius:12px;border:1px solid #dbeafe;max-height:560px;overflow:auto;scroll-behavior:smooth;}",
        ".tree-wrap details{margin:6px 0 6px 14px;}",
        ".tree-wrap summary{cursor:pointer;line-height:1.5;}",
        ".tree-wrap .node-pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;color:#fff;margin-left:8px;}",
        ".tree-wrap .tmpl{padding:8px;border:1px solid #e2e8f0;border-radius:10px;background:#ffffff;}",
        ".tree-wrap .tmpl.current{border-color:#0ea5e9;box-shadow:0 0 0 2px rgba(14,165,233,.2);}",
        ".tree-wrap .meta{color:#334155;font-size:12px;margin-top:6px;}",
        ".tree-wrap .src-badge{display:inline-block;color:#fff;padding:1px 6px;border-radius:999px;font-size:11px;margin-left:8px;}",
        ".tree-wrap .inst{padding:6px 8px;background:#f1f5f9;border-radius:8px;margin:4px 0;font-size:12px;}",
        ".tree-wrap .debug{margin-top:6px;padding:8px;background:#0f172a;color:#e2e8f0;border-radius:8px;font-size:11px;white-space:pre-wrap;}",
        "</style>",
        "<div class='tree-wrap'>",
        f"<div><strong>Template Tree</strong> | Latest Batch: {latest_batch_id} | Logs: {tree.get('total_logs', 0)}</div>",
    ]

    if not levels:
        parts.append("<div style='margin-top:8px;'>No tree data available. Run a parse first.</div></div>")
        return "".join(parts)

    for level_name, level_data in levels.items():
        color = _LEVEL_COLORS.get(level_name, "#475569")
        parts.append("<details open>")
        parts.append(
            f"<summary><strong>{html.escape(level_name)}</strong><span class='node-pill' style='background:{color};'>{html.escape(level_name)}</span></summary>"
        )

        event_types = level_data.get("event_types", {})
        for event_name, event_data in event_types.items():
            parts.append("<details>")
            parts.append(f"<summary>Event: <strong>{html.escape(event_name)}</strong></summary>")

            for template in event_data.get("templates", []):
                current = bool(template.get("highlight_current_batch", False) and show_current_batch)
                current_cls = " current" if current else ""
                cache_pct = template.get("source", {}).get("cache_pct", 0)
                slm_pct = template.get("source", {}).get("slm_pct", 0)
                current_count = template.get("current_batch_count", 0)

                parts.append(f"<details class='tmpl{current_cls}'>")
                summary = (
                    f"<summary>{html.escape(template.get('template_text', ''))} "
                    f"<span class='meta'>count={template.get('count', 0)}</span>"
                    f"<span class='src-badge' style='background:#16a34a;'>CACHE {cache_pct}%</span>"
                    f"<span class='src-badge' style='background:#7e22ce;'>SLM {slm_pct}%</span>"
                )
                if current and current_count:
                    summary += f"<span class='src-badge' style='background:#0ea5e9;'>Current Batch {current_count}</span>"
                summary += "</summary>"
                parts.append(summary)

                parts.append("<div class='meta'>")
                parts.append(f"usage_count(global): {template.get('global_count', 0)}<br>")
                parts.append(f"first_seen: {html.escape(str(template.get('first_seen', '')))}<br>")
                parts.append(f"last_seen: {html.escape(str(template.get('last_seen', '')))}")
                parts.append("</div>")

                examples = template.get("example_logs", [])
                if examples:
                    parts.append("<div class='meta'><strong>Examples:</strong><ul>")
                    for ex in examples:
                        parts.append(f"<li>{html.escape(ex)}</li>")
                    parts.append("</ul></div>")

                parts.append("<details><summary>Instances</summary>")
                for instance in template.get("instances", []):
                    src = str(instance.get("source", "SLM"))
                    parts.append("<div class='inst'>")
                    parts.append(_source_badge(src))
                    parts.append(f" {html.escape(str(instance.get('original_log', '')))}")
                    parts.append("</div>")

                if template.get("instances_truncated", False):
                    parts.append(
                        f"<div class='meta'>Lazy loading active: {template.get('omitted_instances', 0)} additional instances not rendered.</div>"
                    )
                parts.append("</details>")

                if debug_mode:
                    debug = template.get("debug", {})
                    dbg_lines = [
                        f"cluster_ids: {debug.get('cluster_ids', [])}",
                        f"cache_hit: {debug.get('cache_hit', 0)}",
                        f"cache_miss: {debug.get('cache_miss', 0)}",
                        f"raw_slm_output: {debug.get('raw_slm_outputs', [])}",
                    ]
                    parts.append(f"<div class='debug'>{html.escape(chr(10).join(dbg_lines))}</div>")

                parts.append("</details>")

            parts.append("</details>")

        parts.append("</details>")

    parts.append("</div>")
    return "".join(parts)
