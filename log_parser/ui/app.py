from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gradio as gr

from log_parser.config import load_config
from log_parser.factory import build_pipeline
from log_parser.pipeline.tree_data import build_template_tree
from log_parser.ui.tree_renderer import render_tree_html


def create_ui(config_path: str | Path = "log_parser/configs/config.yaml") -> gr.Blocks:
    pipeline, cfg = build_pipeline(config_path)
    
    # Get database reference for loading previous data
    cache_db = pipeline.cache.get_db()

    def _template_markdown(stats: list[dict[str, Any]]) -> str:
        if not stats:
            return "No templates recorded yet."
        lines = ["### Template Viewer", ""]
        for item in stats:
            ratio = item["source_ratio"]
            lines.append(f"- Template: {item['template_text']}")
            lines.append(f"  - usage_count: {item['usage_count']}")
            lines.append(f"  - last_used: {item['last_used']}")
            lines.append(f"  - example_log: {item['example_log']}")
            lines.append(
                f"  - source_ratio: CACHE {ratio['cache_pct']}% | SLM {ratio['slm_pct']}%"
            )
        return "\n".join(lines)

    def _batch_summary(trace: dict[str, Any]) -> str:
        if not trace.get("batches"):
            return "No batch data available."

        lines = ["### Batch Analysis"]
        for batch in trace["batches"]:
            lines.append(
                f"Batch {batch['batch_id']} | cluster_id={batch['cluster_id']} | total_logs={batch['number_of_logs']} | source={batch['source']} | processing_time_ms={batch['processing_time_ms']}"
            )
            local_dist: dict[str, int] = {}
            for item in batch["logs"]:
                local_dist[item["template"]] = local_dist.get(item["template"], 0) + 1
            for template, count in local_dist.items():
                lines.append(f"  {template} -> {count} logs")
        return "\n".join(lines)

    def _parse(
        text: str,
        show_current_batch: bool,
        debug_mode: bool,
        instance_limit: int,
    ) -> tuple[str, str, str, list[list[Any]], list[list[Any]], str, str, dict[str, Any]]:
        logs = [line.strip() for line in text.splitlines() if line.strip()]
        if not logs:
            empty_tree = {
                "generated_at": "",
                "latest_batch_id": 0,
                "show_current_batch": show_current_batch,
                "debug_mode": debug_mode,
                "total_logs": 0,
                "levels": {},
            }
            return (
                "",
                "No templates recorded yet.",
                "No batch data available.",
                [],
                [],
                "",
                render_tree_html(empty_tree, show_current_batch, debug_mode),
                empty_tree,
            )

        templates = pipeline.run(logs)

        trace = pipeline.get_last_trace().to_dict()
        stats = pipeline.get_template_stats()
        tree_data = build_template_tree(
            trace=trace,
            template_stats=stats,
            show_current_batch=show_current_batch,
            debug_mode=debug_mode,
            instance_limit=instance_limit,
        )
        tree_html = render_tree_html(tree_data, show_current_batch, debug_mode)

        # Save tree snapshot to database
        if cache_db:
            try:
                latest_batch_id = tree_data.get("latest_batch_id", 0)
                total_logs = tree_data.get("total_logs", 0)
                cache_db.save_tree_snapshot(tree_data, batch_id=latest_batch_id, total_logs=total_logs)
            except Exception as e:
                print(f"Warning: Failed to save tree snapshot: {e}")

        source_rows: list[list[Any]] = []
        for stat in stats:
            ratio = stat["source_ratio"]
            source_rows.append(
                [stat["template_text"], stat["usage_count"], ratio["cache_pct"], ratio["slm_pct"]]
            )

        structure_rows: list[list[Any]] = []
        for batch in trace.get("batches", []):
            for item in batch.get("logs", []):
                structure_rows.append(
                    [
                        item["text"],
                        item["masked"],
                        item["level"],
                        item["event_type"],
                        item["source"],
                    ]
                )

        debug_payload = json.dumps(trace, indent=2) if debug_mode else ""
        return (
            "\n".join(templates),
            _template_markdown(stats),
            _batch_summary(trace),
            source_rows,
            structure_rows,
            debug_payload,
            tree_html,
            tree_data,
        )

    def _load_previous() -> tuple[str, dict[str, Any]]:
        """Load the most recent tree snapshot from database."""
        if not cache_db:
            return "No database available.", {}
        
        try:
            tree_data = cache_db.get_latest_tree_snapshot()
            if tree_data:
                tree_html = render_tree_html(
                    tree_data,
                    show_current_batch=tree_data.get("show_current_batch", True),
                    debug_mode=tree_data.get("debug_mode", False)
                )
                return tree_html, tree_data
            else:
                return "No previous tree snapshots found.", {}
        except Exception as e:
            return f"Error loading previous tree: {e}", {}

    def _load_cache_stats() -> str:
        """Load cache statistics."""
        if not cache_db:
            return "No database available."
        
        try:
            stats = cache_db.get_template_stats()
            if not stats:
                return "No cached templates yet."
            
            lines = ["# Persistent Cache Statistics", ""]
            lines.append(f"Total cached templates: {len(stats)}")
            lines.append("")
            for stat in stats[:10]:  # Show top 10
                lines.append(f"## {stat['template_text']}")
                lines.append(f"- Usage count: {stat['usage_count']}")
                lines.append(f"- Cache hits: {stat['cache_count']}")
                lines.append(f"- SLM generated: {stat['slm_count']}")
                lines.append(f"- First seen: {stat['first_seen']}")
                lines.append(f"- Last seen: {stat['last_used']}")
                lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Error loading cache stats: {e}"

    with gr.Blocks(title="LogBatcher SLM Parser") as demo:
        gr.Markdown("# LogBatcher - Observable Log Intelligence Platform")
        gr.Markdown("*Database persistence enabled - Tree and cache data are automatically saved and restored*")
        
        with gr.Row():
            with gr.Column():
                input_box = gr.Textbox(label="Input Logs", lines=10, placeholder="One log line per row")
            with gr.Column():
                with gr.Group():
                    gr.Markdown("### Controls")
                    show_current_batch = gr.Checkbox(label="Show Current Batch", value=True)
                    debug_mode = gr.Checkbox(label="Debug Mode", value=False)
                    instance_limit = gr.Slider(
                        label="Lazy Instance Limit Per Template",
                        minimum=5,
                        maximum=200,
                        value=25,
                        step=1,
                    )
                    run_btn = gr.Button("Parse Logs", scale=2)
                    
                with gr.Group():
                    gr.Markdown("### Previous Data")
                    load_previous_btn = gr.Button("Load Previous Tree", size="sm")
                    load_cache_btn = gr.Button("Load Cache Stats", size="sm")

        with gr.Tab("Template Tree"):
            tree_html_view = gr.HTML(label="Template Tree Visualization")
            tree_json_view = gr.JSON(label="Tree Data")

        with gr.Tab("Templates"):
            templates_output = gr.Textbox(label="Parsed Templates", lines=8)
            template_viewer = gr.Markdown(label="Template Viewer")

        with gr.Tab("Batch Analysis"):
            batch_summary = gr.Textbox(label="Batch Analysis", lines=12)
            source_table = gr.Dataframe(
                headers=["template_text", "usage_count", "cache_pct", "slm_pct"],
                label="Source Visualization",
                interactive=False,
            )

        with gr.Tab("Log Structure"):
            structure_table = gr.Dataframe(
                headers=["original_log", "masked_log", "log_level", "event_type", "source"],
                label="Log Structure Extraction",
                interactive=False,
            )

        with gr.Tab("Debug"):
            debug_json = gr.Code(label="Debug Trace (clusters/cache/SLM raw)", language="json")

        with gr.Tab("Cache Statistics"):
            cache_stats = gr.Markdown(label="Cache Statistics")

        run_btn.click(
            fn=_parse,
            inputs=[input_box, show_current_batch, debug_mode, instance_limit],
            outputs=[
                templates_output,
                template_viewer,
                batch_summary,
                source_table,
                structure_table,
                debug_json,
                tree_html_view,
                tree_json_view,
            ],
        )

        load_previous_btn.click(
            fn=_load_previous,
            outputs=[tree_html_view, tree_json_view],
        )

        load_cache_btn.click(
            fn=_load_cache_stats,
            outputs=[cache_stats],
        )

        # Load and display previous tree on startup
        demo.load(
            fn=_load_previous,
            outputs=[tree_html_view, tree_json_view],
        )

    return demo


def launch_ui(config_path: str | Path = "log_parser/configs/config.yaml") -> None:
    demo = create_ui(config_path)
    cfg = load_config(config_path)
    demo.launch(server_port=cfg.ui_port)
