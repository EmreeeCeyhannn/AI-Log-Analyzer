from __future__ import annotations

from abc import ABC, abstractmethod
import re
from dataclasses import dataclass
from typing import List

from log_parser.models.slm_model import SLMModel
from log_parser.pipeline.postprocess import TemplatePostProcessor


class BaseParser(ABC):
    """Contract for parser implementations."""

    @abstractmethod
    def parse(self, logs: List[str]) -> str:
        """Parses a batch of logs into a single template string."""

    def parse_with_details(self, logs: List[str]) -> "ParseDetails":
        template = self.parse(logs)
        return ParseDetails(template=template, raw_output=template, used_fallback=False)


@dataclass
class ParseDetails:
    template: str
    raw_output: str
    used_fallback: bool


class SLMParser(BaseParser):
    """SLM-backed parser implementation with deterministic generation."""

    def __init__(self, model: SLMModel, post_processor: TemplatePostProcessor) -> None:
        self.model = model
        self.post_processor = post_processor

    def parse(self, logs: List[str]) -> str:
        return self.parse_with_details(logs).template

    def parse_with_details(self, logs: List[str]) -> ParseDetails:
        if not logs:
            return ParseDetails(template="", raw_output="", used_fallback=False)

        prompt = self._build_prompt(logs)
        try:
            raw_output = self.model.generate(prompt)
            template = self._extract_template(raw_output)
            used_fallback = False
        except Exception:
            # Keep service available even if model path/config is invalid.
            raw_output = ""
            template = self._heuristic_template(logs)
            used_fallback = True
        normalized = self.post_processor.normalize(template)
        return ParseDetails(template=normalized, raw_output=raw_output, used_fallback=used_fallback)

    @staticmethod
    def _build_prompt(logs: List[str]) -> str:
        examples = "\n".join(f"- {line}" for line in logs)
        return (
            "You are a deterministic log template extractor.\n"
            "Given log lines that share the same event pattern, produce exactly one template.\n"
            "Rules:\n"
            "1) Keep static words unchanged.\n"
            "2) Replace dynamic values (numbers, ids, IPs, UUIDs, timestamps) with <*>.\n"
            "3) Return only the template line and nothing else.\n\n"
            f"Logs:\n{examples}\n\n"
            "Template:\n"
        )

    @staticmethod
    def _extract_template(output: str) -> str:
        line = output.splitlines()[0] if output else ""
        line = line.replace("Template:", "").strip()
        if line.startswith("- "):
            line = line[2:].strip()
        return line

    @staticmethod
    def _heuristic_template(logs: List[str]) -> str:
        if not logs:
            return ""

        base = logs[0]
        patterns = [
            re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
            re.compile(r"\b0x[0-9a-fA-F]+\b"),
            re.compile(r"\b\d+\b"),
            re.compile(
                r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
            ),
        ]

        for pattern in patterns:
            base = pattern.sub("<*>", base)
        return base
