from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

_LOGGER_NAME = "log_parser"
_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    """Formats log records as one-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
        }
        extra_payload = getattr(record, "payload", None)
        if isinstance(extra_payload, dict):
            payload.update(extra_payload)
        return json.dumps(payload, ensure_ascii=True)


def setup_logging(log_file_path: str = "logs/system.log") -> logging.Logger:
    """Configures console + file JSON logging once for the application."""
    global _CONFIGURED

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)

    if _CONFIGURED:
        return logger

    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = JsonFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    _CONFIGURED = True
    return logger


def emit(logger: logging.Logger, message: str, payload: Dict[str, Any]) -> None:
    """Writes a structured JSON event."""
    logger.info(message, extra={"payload": payload})
