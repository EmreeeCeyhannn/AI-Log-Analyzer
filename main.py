from __future__ import annotations

import argparse

from log_parser.api.fastapi_app import create_app
from log_parser.factory import build_pipeline
from log_parser.ui.app import launch_ui


def main() -> None:
    parser = argparse.ArgumentParser(description="LogBatcher production SLM parser")
    parser.add_argument("--mode", choices=["cli", "api", "ui"], default="cli")
    parser.add_argument("--config", default="log_parser/configs/config.yaml")
    parser.add_argument("--logs", nargs="*", default=[])
    args = parser.parse_args()

    if args.mode == "api":
        import uvicorn

        app = create_app(args.config)
        _, cfg = build_pipeline(args.config)
        uvicorn.run(app, host=cfg.api_host, port=cfg.api_port)
        return

    if args.mode == "ui":
        launch_ui(args.config)
        return

    pipeline, _ = build_pipeline(args.config)
    if not args.logs:
        print("Provide logs with --logs for CLI mode, or use --mode api/ui")
        return

    templates = pipeline.run(args.logs)
    for template in templates:
        print(template)


if __name__ == "__main__":
    main()
