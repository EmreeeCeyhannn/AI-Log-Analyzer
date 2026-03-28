from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Cluster:
    """Represents a cluster of semantically similar logs."""

    cluster_id: str
    indices: List[int]
    logs: List[str]


class LogClusterer:
    """Clusters logs by normalized structural signatures."""

    _ip_pattern = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
    _hex_pattern = re.compile(r"\b0x[0-9a-fA-F]+\b")
    _num_pattern = re.compile(r"\b\d+\b")
    _guid_pattern = re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    )

    def __init__(self, min_tokens: int = 3) -> None:
        self.min_tokens = min_tokens

    def cluster(self, logs: List[str]) -> List[Cluster]:
        grouped: Dict[str, List[int]] = defaultdict(list)
        for idx, log in enumerate(logs):
            grouped[self.signature(log)].append(idx)

        clusters: List[Cluster] = []
        for cid, indices in grouped.items():
            clusters.append(
                Cluster(cluster_id=cid, indices=indices, logs=[logs[i] for i in indices])
            )
        return clusters

    def signature(self, log: str) -> str:
        normalized = log.lower().strip()
        normalized = self._guid_pattern.sub("<guid>", normalized)
        normalized = self._ip_pattern.sub("<ip>", normalized)
        normalized = self._hex_pattern.sub("<hex>", normalized)
        normalized = self._num_pattern.sub("<num>", normalized)

        tokens = normalized.split()
        if len(tokens) < self.min_tokens:
            return " ".join(tokens)
        return " ".join(tokens[: self.min_tokens])
