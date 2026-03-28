# LogBatcher (Observable SLM Platform)

This project is a modular, production-focused log intelligence platform that uses local HuggingFace-compatible SLM inference (no external LLM API calls), while preserving clustering, batching, and caching.

## Folder Structure

```text
log_parser/
  pipeline/
    pipeline.py
    clustering.py
    cache.py
    parser.py
    postprocess.py
    analysis.py
    intelligence.py
    tree_data.py
  models/
    slm_model.py
  api/
    fastapi_app.py
  ui/
    app.py
    tree_renderer.py
  configs/
    config.yaml
  config.py
  observability.py
  factory.py
main.py
AUDIT_REPORT.md
examples/
  tree_example.json
requirements.txt
```

## Key Production Capabilities

- Local SLM wrapper with deterministic generation settings.
- No external model API providers.
- Preserved core flow: clustering -> cache -> SLM parsing -> cache store -> output.
- Structured JSON observability to console and `logs/system.log`.
- Batch and per-log trace capture:
  - `batch_id`, `cluster_id`, `number_of_logs`, `processing_time_ms`
  - Per-log `text`, `template`, `source`, `level`, `event_type`, `masked`
- Template intelligence registry:
  - `template_text`, `usage_count`, `last_used`, `source_ratio`
- API + dashboard-ready introspection endpoints and UI tabs.
- Hierarchical template tree model grouped by log level -> event -> template -> instances.
- Batch overlay highlighting for latest batch templates.
- Debug-mode tree details with cluster IDs, cache hit/miss, and raw SLM output snippets.

## Install

```bash
pip install -r requirements.txt
```

## Configure

Edit `log_parser/configs/config.yaml`:

```yaml
model:
  name_or_path: "distilgpt2"
  max_new_tokens: 64

pipeline:
  batch_size: 16
  min_cluster_tokens: 3

api:
  host: "127.0.0.1"
  port: 8000

observability:
  log_file_path: "logs/system.log"

ui:
  port: 7860
```

## Run

### CLI

```bash
python main.py --mode cli --logs "User 42 logged in from 10.0.0.1" "User 51 logged in from 10.0.0.2"
```

### API

```bash
python main.py --mode api
```

### UI

```bash
python main.py --mode ui
```

## API Example

### `POST /parse`

Request:

```json
{
	"logs": ["User 42 logged in from 10.0.0.1", "User 51 logged in from 10.0.0.2"]
}
```

Response:

```json
{
	"templates": ["User <*> logged in from <*>", "User <*> logged in from <*>"]
}
```

### `POST /parse?debug=true`

Includes run trace payload:

```json
{
	"templates": ["User <*> logged in from <*>", "User <*> logged in from <*>"],
	"trace": {
		"total_logs": 2,
		"batch_count": 1,
		"template_count": 1,
		"distribution": { "User <*> logged in from <*>": 2 },
		"batches": [
			{
				"batch_id": 1,
				"cluster_id": "user <num> logged",
				"source": "SLM",
				"processing_time_ms": 125.31,
				"logs": [
					{
						"text": "INFO User 42 logged in from 10.0.0.1",
						"template": "User <*> logged in from <*>",
						"source": "SLM",
						"level": "INFO",
						"event_type": "AUTH",
						"masked": "INFO User <*> logged in from <*>"
					}
				]
			}
		]
	}
}
```

### `GET /batches/latest`

Returns the latest run trace.

### `GET /templates/stats`

Returns global template intelligence stats with source ratios.

### `GET /templates/tree`

Returns hierarchical tree data for visualization.

Query params:

- `show_current_batch` (bool): highlight templates from latest batch
- `debug` (bool): include cluster/cache/SLM debug payload
- `instance_limit` (int): lazy instance window per template

Shape:

```json
{
	"levels": {
		"INFO": {
			"event_types": {
				"login": {
					"templates": [
						{
							"template_text": "User <*> logged in from <*>",
							"count": 120,
							"source": {
								"cache": 80,
								"slm": 40,
								"cache_pct": 66.67,
								"slm_pct": 33.33
							},
							"instances": [
								{
									"original_log": "INFO User 123 logged in from 10.0.0.1",
									"source": "CACHE"
								}
							]
						}
					]
				}
			}
		}
	}
}
```

### `GET /templates/tree/example`

Returns static sample tree dataset from `examples/tree_example.json`.

### `POST /classify`

Request:

```json
{
	"template": "Disk error on node <*>"
}
```

Response:

```json
{
	"label": "error"
}
```

## UI Dashboard

`--mode ui` launches an interactive dashboard with tabs:

- Template Tree: expandable/collapsible hierarchy
  - Level colors: INFO blue, WARN orange, ERROR red
  - Source badges: CACHE green, SLM purple
  - Template detail panel on expand: count, first seen, last seen, examples
  - Instance expansion with source labels
  - Lazy rendering via configurable instance limit
- Show Current Batch toggle: highlights templates active in latest batch and displays current-batch counts
- Debug Mode toggle: surfaces cluster_id, cache hit/miss totals, and raw SLM output fragments

- Templates: parsed output + template viewer
- Batch Analysis: per-batch stats + template distribution
- Log Structure: masked logs with detected level/event
- Debug: full run trace including cluster IDs, cache/SLM source, and raw SLM output

## Notes for Production

- Replace `model.name_or_path` with your fine-tuned local HF path.
- For multi-instance deployment, replace in-memory cache/intelligence with Redis/Postgres.
- Add auth/rate-limits for API and export logs to your SIEM stack.

## Research Context

This implementation aligns with the capstone concept:

**SLM-Based Resource Efficient Log Analysis System**

Core research goals reflected in this project:

- SLM-first local inference for low-latency operation.
- Micro-batch style processing to reduce model calls.
- Evidence-first template extraction and structured run tracing.
- Basis for RCA and future predictive maintenance integrations.

## Abstract

This project presents a conceptual architecture for a Resource-Efficient AIOps pipeline designed to analyze high-volume system logs using Small Language Models (SLMs).

While Large Language Models (LLMs) offer strong performance in log analysis, they often suffer from high latency and operational costs in online scenarios. To address this, this system proposes an end-to-end pipeline that integrates micro-batching, retrieval-augmented patterns, and predictive extensions to provide real-time anomaly detection and root-cause support without the heavy computational burden of giant models.

## Operational Workflow (Research View)

| Stage | Input | Expected Output |
| :--- | :--- | :--- |
| 1. Micro-Batching | Raw log stream (time/line window) | Batch ID + Raw Lines |
| 2. Parsing | Raw logs within batch | Log templates + parameters |
| 3. Embedding | Log templates | Vector representations |
| 4. Retrieval | Current vector | Similar historical incidents |
| 5. Detection | Template sequence + scores | Anomaly label |
| 6. Summarization | Evidence + metadata | Event summary |
| 7. RCA Support | Summary + retrieved context | Root-cause hypotheses |
| 8. Early Warning | Time-series history | Risk alert |

## Authors

- Emre Ceyhan
- Kutlu Turkuçu

LinkedIn: www.linkedin.com/in/emre-ceyhan-02602b304
