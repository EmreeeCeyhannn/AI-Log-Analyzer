from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class AppConfig:
    model_name_or_path: str
    batch_size: int
    min_cluster_tokens: int
    max_new_tokens: int
    api_host: str
    api_port: int
    log_file_path: str
    ui_port: int


def load_config(config_path: str | Path) -> AppConfig:
    with Path(config_path).open("r", encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f)

    model = raw.get("model", {})
    pipeline = raw.get("pipeline", {})
    api = raw.get("api", {})
    observability = raw.get("observability", {})
    ui = raw.get("ui", {})

    return AppConfig(
        model_name_or_path=model.get("name_or_path", "distilgpt2"),
        batch_size=int(pipeline.get("batch_size", 16)),
        min_cluster_tokens=int(pipeline.get("min_cluster_tokens", 3)),
        max_new_tokens=int(model.get("max_new_tokens", 64)),
        api_host=str(api.get("host", "127.0.0.1")),
        api_port=int(api.get("port", 8000)),
        log_file_path=str(observability.get("log_file_path", "logs/system.log")),
        ui_port=int(ui.get("port", 7860)),
    )
