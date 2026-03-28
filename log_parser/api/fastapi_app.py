from __future__ import annotations

from pathlib import Path
import json
from typing import Any, List

from fastapi import FastAPI
from pydantic import BaseModel, Field

from log_parser.factory import build_pipeline
from log_parser.pipeline.tree_data import build_template_tree


class ParseRequest(BaseModel):
    logs: List[str] = Field(..., min_length=1)


class ParseResponse(BaseModel):
    templates: List[str]
    trace: dict[str, Any] | None = None


class ClassifyRequest(BaseModel):
    template: str


class ClassifyResponse(BaseModel):
    label: str


def create_app(config_path: str | Path = "log_parser/configs/config.yaml") -> FastAPI:
    app = FastAPI(title="LogBatcher SLM Parser", version="1.0.0")
    pipeline, cfg = build_pipeline(config_path)

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "model": cfg.model_name_or_path,
            "log_file": cfg.log_file_path,
        }

    @app.post("/parse", response_model=ParseResponse)
    def parse_logs(payload: ParseRequest, debug: bool = False) -> ParseResponse:
        templates = pipeline.run(payload.logs)
        trace = pipeline.get_last_trace().to_dict() if debug else None
        return ParseResponse(templates=templates, trace=trace)

    @app.get("/batches/latest")
    def latest_batch_trace() -> dict[str, Any]:
        return pipeline.get_last_trace().to_dict()

    @app.get("/templates/stats")
    def template_stats() -> list[dict[str, Any]]:
        return pipeline.get_template_stats()

    @app.get("/templates/tree")
    def template_tree(
        show_current_batch: bool = True,
        debug: bool = False,
        instance_limit: int = 25,
    ) -> dict[str, Any]:
        trace = pipeline.get_last_trace().to_dict()
        stats = pipeline.get_template_stats()
        return build_template_tree(
            trace=trace,
            template_stats=stats,
            show_current_batch=show_current_batch,
            debug_mode=debug,
            instance_limit=max(1, min(instance_limit, 500)),
        )

    @app.get("/templates/tree/example")
    def template_tree_example() -> dict[str, Any]:
        sample_path = Path("examples/tree_example.json")
        return json.loads(sample_path.read_text(encoding="utf-8"))

    @app.post("/classify", response_model=ClassifyResponse)
    def classify(payload: ClassifyRequest) -> ClassifyResponse:
        # Placeholder for future template classifier integration.
        text = payload.template.lower()
        label = "error" if any(k in text for k in ["error", "fail", "exception"]) else "normal"
        return ClassifyResponse(label=label)

    return app


app = create_app()
