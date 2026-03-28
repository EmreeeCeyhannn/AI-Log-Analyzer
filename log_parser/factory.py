from __future__ import annotations

from pathlib import Path

from log_parser.config import AppConfig, load_config
from log_parser.models.slm_model import SLMModel, SLMSettings
from log_parser.observability import setup_logging
from log_parser.pipeline.cache import TemplateCache
from log_parser.pipeline.clustering import LogClusterer
from log_parser.pipeline.db import TemplateDatabase
from log_parser.pipeline.intelligence import TemplateIntelligenceRegistry
from log_parser.pipeline.parser import SLMParser
from log_parser.pipeline.pipeline import LogPipeline, PipelineConfig
from log_parser.pipeline.postprocess import TemplatePostProcessor


def build_pipeline(config_path: str | Path) -> tuple[LogPipeline, AppConfig]:
    cfg = load_config(config_path)
    logger = setup_logging(cfg.log_file_path)

    # Initialize database for persistence
    db = TemplateDatabase(db_path="log_parser/data/templates.db")

    model = SLMModel(
        SLMSettings(
            model_name_or_path=cfg.model_name_or_path,
            max_new_tokens=cfg.max_new_tokens,
        )
    )
    parser = SLMParser(model=model, post_processor=TemplatePostProcessor())

    # Create cache with database support
    cache = TemplateCache(db_path="log_parser/data/templates.db")

    # Create registry with database support
    registry = TemplateIntelligenceRegistry()
    registry.set_db(db)

    pipeline = LogPipeline(
        clusterer=LogClusterer(min_tokens=cfg.min_cluster_tokens),
        cache=cache,
        parser=parser,
        config=PipelineConfig(batch_size=cfg.batch_size),
        logger=logger,
        registry=registry,
    )
    return pipeline, cfg
