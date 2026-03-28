from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import logging
from time import perf_counter
from typing import List

from log_parser.observability import emit
from log_parser.pipeline.cache import TemplateCache
from log_parser.pipeline.analysis import detect_event_type, detect_log_level, mask_dynamic_parts
from log_parser.pipeline.clustering import LogClusterer
from log_parser.pipeline.intelligence import TemplateIntelligenceRegistry
from log_parser.pipeline.parser import BaseParser


@dataclass
class PipelineConfig:
    batch_size: int = 16


@dataclass
class LogTrace:
    text: str
    template: str
    source: str
    level: str
    event_type: str
    masked: str

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "template": self.template,
            "source": self.source,
            "level": self.level,
            "event_type": self.event_type,
            "masked": self.masked,
        }


@dataclass
class BatchTrace:
    batch_id: int
    cluster_id: str
    number_of_logs: int
    processing_time_ms: float
    cache_key: str
    source: str
    slm_raw_output: str
    logs: List[LogTrace]

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "cluster_id": self.cluster_id,
            "number_of_logs": self.number_of_logs,
            "processing_time_ms": round(self.processing_time_ms, 3),
            "cache_key": self.cache_key,
            "source": self.source,
            "slm_raw_output": self.slm_raw_output,
            "logs": [item.to_dict() for item in self.logs],
        }


@dataclass
class RunTrace:
    batches: List[BatchTrace]

    def to_dict(self) -> dict:
        distribution: Counter[str] = Counter()
        total_logs = 0
        for batch in self.batches:
            for item in batch.logs:
                distribution[item.template] += 1
                total_logs += 1

        return {
            "total_logs": total_logs,
            "batch_count": len(self.batches),
            "template_count": len(distribution),
            "distribution": dict(distribution),
            "batches": [batch.to_dict() for batch in self.batches],
        }


class LogPipeline:
    """Main orchestration pipeline: cluster -> cache -> parse -> cache store -> output."""

    def __init__(
        self,
        clusterer: LogClusterer,
        cache: TemplateCache,
        parser: BaseParser,
        config: PipelineConfig,
        logger: logging.Logger,
        registry: TemplateIntelligenceRegistry,
    ) -> None:
        self.clusterer = clusterer
        self.cache = cache
        self.parser = parser
        self.config = config
        self.logger = logger
        self.registry = registry
        self._last_trace = RunTrace(batches=[])

    def run(self, logs: List[str]) -> List[str]:
        templates: List[str] = [""] * len(logs)
        clusters = self.clusterer.cluster(logs)
        traces: List[BatchTrace] = []
        batch_id = 0

        for cluster in clusters:
            for batch_indices in self._batched_indices(cluster.indices, self.config.batch_size):
                batch_id += 1
                started_at = perf_counter()
                batch_logs = [logs[i] for i in batch_indices]
                cache_key = self.cache.key_from_signature(cluster.cluster_id, batch_logs)
                source = "CACHE"
                slm_raw_output = ""

                template = self.cache.get(cache_key)
                if template is None:
                    source = "SLM"
                    details = self.parser.parse_with_details(batch_logs)
                    template = details.template
                    slm_raw_output = details.raw_output
                    self.cache.set(cache_key, template)

                log_traces: List[LogTrace] = []
                for idx in batch_indices:
                    original = logs[idx]
                    templates[idx] = template
                    trace_item = LogTrace(
                        text=original,
                        template=template,
                        source=source,
                        level=detect_log_level(original),
                        event_type=detect_event_type(original),
                        masked=mask_dynamic_parts(original),
                    )
                    log_traces.append(trace_item)
                    self.registry.record(template=template, source=source, example_log=original)

                elapsed_ms = (perf_counter() - started_at) * 1000.0
                batch_trace = BatchTrace(
                    batch_id=batch_id,
                    cluster_id=cluster.cluster_id,
                    number_of_logs=len(batch_logs),
                    processing_time_ms=elapsed_ms,
                    cache_key=cache_key,
                    source=source,
                    slm_raw_output=slm_raw_output,
                    logs=log_traces,
                )
                traces.append(batch_trace)
                emit(self.logger, "batch_processed", batch_trace.to_dict())

        self._last_trace = RunTrace(batches=traces)
        emit(self.logger, "run_completed", self._last_trace.to_dict())
        return templates

    def get_last_trace(self) -> RunTrace:
        return self._last_trace

    def get_template_stats(self) -> list[dict]:
        return self.registry.snapshot()

    @staticmethod
    def _batched_indices(indices: List[int], batch_size: int) -> List[List[int]]:
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        return [indices[i : i + batch_size] for i in range(0, len(indices), batch_size)]
