from __future__ import annotations

import re


class TemplatePostProcessor:
    """Normalizes raw model output into stable log templates."""

    _variable_patterns = [
        re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
        re.compile(r"\b0x[0-9a-fA-F]+\b"),
        re.compile(r"\b\d+\b"),
        re.compile(
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
        ),
    ]

    def normalize(self, template: str) -> str:
        cleaned = " ".join(template.strip().split())
        for pattern in self._variable_patterns:
            cleaned = pattern.sub("<*>", cleaned)
        cleaned = self._normalize_placeholder_spacing(cleaned)
        return cleaned

    @staticmethod
    def _normalize_placeholder_spacing(text: str) -> str:
        text = re.sub(r"<\s*\*\s*>", "<*>", text)
        text = re.sub(r"(?:<\*>\s*){2,}", "<*> ", text)
        return text.strip()
