from __future__ import annotations

import re


_LEVEL_PATTERNS = {
    "ERROR": re.compile(r"\b(error|exception|fatal|panic|failed?)\b", re.IGNORECASE),
    "WARN": re.compile(r"\b(warn|warning|deprecated|retry)\b", re.IGNORECASE),
    "INFO": re.compile(r"\b(info|started|connected|success|logged in)\b", re.IGNORECASE),
}

_EVENT_PATTERNS = [
    ("AUTH", re.compile(r"\b(login|logout|auth|token|password)\b", re.IGNORECASE)),
    ("NETWORK", re.compile(r"\b(timeout|connection|socket|dns|http)\b", re.IGNORECASE)),
    ("DB", re.compile(r"\b(sql|database|db|query|transaction)\b", re.IGNORECASE)),
    ("SYSTEM", re.compile(r"\b(cpu|memory|disk|node|service|process)\b", re.IGNORECASE)),
]

_MASK_PATTERNS = [
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    re.compile(r"\b\d+\b"),
    re.compile(r"\b0x[0-9a-fA-F]+\b"),
    re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
]


def detect_log_level(text: str) -> str:
    for level, pattern in _LEVEL_PATTERNS.items():
        if pattern.search(text):
            return level
    return "INFO"


def detect_event_type(text: str) -> str:
    for event_name, pattern in _EVENT_PATTERNS:
        if pattern.search(text):
            return event_name
    return "GENERIC"


def mask_dynamic_parts(text: str) -> str:
    masked = text
    for pattern in _MASK_PATTERNS:
        masked = pattern.sub("<*>", masked)
    return masked
