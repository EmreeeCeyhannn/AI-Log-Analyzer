# LogBatcher - Observable SLM Log Intelligence Platform

## Complete Project Documentation

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Design](#architecture--design)
3. [Key Components](#key-components)
4. [Data Flow Pipeline](#data-flow-pipeline)
5. [Tree Structure & Storage](#tree-structure--storage)
6. [Database Persistence](#database-persistence)
7. [How It Works - Detailed](#how-it-works---detailed)
8. [API Reference](#api-reference)
9. [UI Dashboard](#ui-dashboard)
10. [Configuration](#configuration)
11. [Usage Examples](#usage-examples)
12. [Observability & Logging](#observability--logging)

---

## Project Overview

**LogBatcher** is a production-focused **log intelligence platform** that uses local Small Language Models (SLM) for log parsing, clustering, and template extraction. Unlike solutions that rely on external LLM APIs, LogBatcher runs completely local inference using HuggingFace-compatible models.

### Core Features

- **Local SLM Inference**: Deterministic template generation using models like DistilGPT2
- **Intelligent Clustering**: Groups semantically similar logs before processing
- **Caching Layer**: Reduces redundant SLM calls by caching templates
- **Structured Observability**: JSON-based tracing for audit and debugging
- **Multiple Interfaces**: CLI, REST API, and web-based Gradio dashboard
- **Hierarchical Tree Model**: Organizes templates by log level, event type, and content
- **Persistent Storage**: SQLite database for templates, cache, and stats
- **Batch Processing**: Optimized batching for efficient throughput

### What It Does

1. Takes raw log lines as input
2. Groups similar logs into clusters
3. Generates template patterns for each cluster using SLM
4. Stores templates in cache and database
5. Provides insights through tree visualization
6. Tracks usage statistics and performance metrics

---

## Architecture & Design

### High-Level Design Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                      INPUT (Log Lines)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Log Clustering        │
              │  (Normalize + Group)   │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Template Cache        │
              │  (Check for Hits)      │
              └────────┬───────────┬───┘
                       │           │
                   CACHE HIT   CACHE MISS
                       │           │
                       │           ▼
                       │    ┌──────────────┐
                       │    │  SLM Parser  │
                       │    │  Generate    │
                       │    │  Template    │
                       │    └──────┬───────┘
                       │           │
                       │           ▼
                       │    ┌──────────────┐
                       │    │  Post-       │
                       │    │  Process     │
                       │    └──────┬───────┘
                       │           │
                       └───────┬───┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Update Stats        │
                    │  + Cache Storage     │
                    │  + Database Persist  │
                    └──────┬───────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │ Tree Building & Output      │
              │ (Organize by Level/Event)   │
              └─────────────────────────────┘
```

### Design Philosophy

- **Modularity**: Each component is independent and testable
- **Deterministic**: SLM uses fixed generation parameters (no sampling)
- **Observable**: All operations are traced and logged
- **Fault-Tolerant**: Falls back to heuristic templates on model errors
- **Thread-Safe**: Uses locks for concurrent access to shared data

---

## Key Components

### 1. **Log Clusterer** (`pipeline/clustering.py`)

**Purpose**: Groups similar logs into clusters before processing.

**How It Works**:

- Normalizes each log (lowercase, strip whitespace)
- Replaces dynamic values with placeholders:
  - GUIDs → `<guid>`
  - IP addresses → `<ip>`
  - Hex values → `<hex>`
  - Numbers → `<num>`
- Extracts signature (first N_min tokens)
- Groups logs with identical signatures

**Example**:

```python
Logs:
  "User 123 logged in from 10.0.0.1"
  "User 456 logged in from 10.0.0.2"
  "User 789 logged in from 10.0.0.3"

Signatures (after normalization):
  "user <num> logged in" (first 3 tokens)

Result: All 3 logs grouped into single cluster
```

**Configuration Parameters**:

- `min_cluster_tokens`: Minimum tokens required for signature (default: 3)

### 2. **Template Cache** (`pipeline/cache.py`)

**Purpose**: Stores and retrieves generated templates to avoid redundant SLM processing.

**Architecture**:

```
┌──────────────────────────┐
│  In-Memory Cache Store   │  (Fast lookup)
│  Dict[cache_key] →       │
│     CacheEntry           │
└──────────────┬───────────┘
               │
        ┌──────▼────────┐
        │  Persistence  │
        │  Layer        │
        └──────┬────────┘
               │
        ┌──────▼──────────────┐
        │  SQLite Database    │
        │  cache_entries      │
        │  (Durable Storage)  │
        └─────────────────────┘
```

**Cache Key Generation**:

```python
cache_key = SHA256(cluster_signature + "\n" + joined_batch_logs)
```

**Operations**:

- `get(key)`: Returns template or None if not found
- `set(key, template)`: Stores in memory and persists to DB

**Persistence**:

- Automatically loads from database on initialization
- All new entries are persisted to SQLite

### 3. **SLM Model Wrapper** (`models/slm_model.py`)

**Purpose**: Interface for local model inference.

**Model Loading**:

- Uses HuggingFace's `AutoModelForCausalLM` and `AutoTokenizer`
- Lazy loading: Model loads only on first call
- Supports any HuggingFace-compatible model

**Generation Settings** (Deterministic):

```python
do_sample: False        # No sampling (greedy decoding)
temperature: 0.0        # No temperature scaling
top_p: 1.0             # No top-p filtering
num_beams: 1           # Beam search disabled
```

**Prompt Template**:

```
You are a deterministic log template extractor.
Given log lines that share the same event pattern, produce exactly one template.
Rules:
1) Keep static words unchanged.
2) Replace dynamic values (numbers, ids, IPs, UUIDs) with <*>.
3) Return only the template line and nothing else.

Logs:
- {log1}
- {log2}
...

Template:
```

### 4. **Post-Processor** (`pipeline/postprocess.py`)

**Purpose**: Normalizes and cleans up raw SLM output.

**Responsibilities**:

- Removes "Template:" prefix if present
- Removes leading "- " if present
- Strips whitespace
- Validates template format

### 5. **Template Intelligence Registry** (`pipeline/intelligence.py`)

**Purpose**: Tracks global template statistics and usage patterns.

**Tracked Statistics** per template:

```
TemplateStats:
  - template_text: The template pattern
  - usage_count: Total logs matching this template
  - cache_count: How many times served from cache
  - slm_count: How many times generated by SLM
  - first_seen: Timestamp of first occurrence
  - last_used: Timestamp of most recent usage
  - example_log: Sample log matching this template
  - source_ratio: Cache % vs SLM % contribution
```

**Database Persistence**:

- Loads existing stats on initialization
- Creates new entries when recording templates
- Updates timestamps and counts in real-time

### 6. **Analysis Module** (`pipeline/analysis.py`)

**Purpose**: Detects log characteristics for tree organization.

**Functions**:

- `detect_log_level()`: Categorizes as ERROR, WARN, or INFO
  - ERROR: error, exception, fatal, panic, failed
  - WARN: warn, warning, deprecated, retry
  - INFO: info, started, connected, success, logged in

- `detect_event_type()`: Categorizes event purpose
  - AUTH: login, logout, auth, token, password
  - NETWORK: timeout, connection, socket, dns, http
  - DB: sql, database, db, query, transaction
  - SYSTEM: cpu, memory, disk, node, service
  - GENERIC: (fallback)

- `mask_dynamic_parts()`: Replaces dynamic values with `<*>`
  - IP addresses, numbers, hex, UUIDs

### 7. **Template Database** (`pipeline/db.py`)

**Purpose**: Persistent storage for cache, templates, and history.

**Schema**:

```sql
-- Cache entries for template lookup
cache_entries {
  id: INTEGER PRIMARY KEY
  cache_key: TEXT UNIQUE
  template_text: TEXT
  created_at: TIMESTAMP
  updated_at: TIMESTAMP
  hit_count: INTEGER
}

-- Template statistics and tracking
template_stats {
  id: INTEGER PRIMARY KEY
  template_text: TEXT UNIQUE
  usage_count: INTEGER
  cache_count: INTEGER
  slm_count: INTEGER
  first_seen: TIMESTAMP
  last_used: TIMESTAMP
  created_at: TIMESTAMP
  updated_at: TIMESTAMP
}

-- Tree history snapshots
tree_history {
  id: INTEGER PRIMARY KEY
  tree_data: TEXT (JSON)
  batch_id: INTEGER
  total_logs: INTEGER
  created_at: TIMESTAMP
}

-- Example logs for reference
example_logs {
  id: INTEGER PRIMARY KEY
  template_text: TEXT
  original_log: TEXT
  log_level: TEXT
  event_type: TEXT
  source: TEXT
  batch_id: INTEGER
  created_at: TIMESTAMP
}
```

---

## Data Flow Pipeline

### Complete Request Processing Flow

```
INPUT: List[str] logs
  │
  ├─► LogPipeline.run(logs)
  │    │
  │    ├─► Clusterer.cluster(logs)
  │    │    └─► Returns: List[Cluster]
  │    │       Each with: cluster_id, indices, logs
  │    │
  │    └─► For each cluster:
  │         │
  │         ├─► Batch logs (size: batch_size)
  │         │
  │         └─► For each batch:
  │              │
  │              ├─► Generate cache_key
  │              │    cache_key = SHA256(signature + batch_logs)
  │              │
  │              ├─► Cache.get(cache_key)
  │              │    ├─ HIT: Get template from cache
  │              │    │        └─ source = "CACHE"
  │              │    │
  │              │    └─ MISS: Parse with SLM
  │              │            ├─ SLMParser.parse_with_details()
  │              │            │  ├─ Build prompt
  │              │            │  ├─ Model.generate()
  │              │            │  ├─ Extract template
  │              │            │  └─ Post-process
  │              │            │
  │              │            ├─ Cache.set(cache_key, template)
  │              │            └─ source = "SLM"
  │              │
  │              └─► For each log in batch:
  │                   ├─ Detect log_level
  │                   ├─ Detect event_type
  │                   ├─ Mask dynamic parts
  │                   ├─ Create LogTrace
  │                   └─ Registry.record(template, source, log)
  │
  ├─► Build trace data (BatchTrace, RunTrace)
  │
  ├─► Emit observability events
  │
  └─► Return: List[str] templates (one per input log)

SIDE EFFECTS:
  ├─ Cache updated in-memory and persisted to DB
  ├─ Template stats updated in Registry
  ├─ Database records created
  └─ Trace data stored for later analysis
```

### Trace Data Structure

Each request produces a `RunTrace` containing:

```python
RunTrace {
  batches: List[BatchTrace] {
    batch_id: int                           # Sequential batch number
    cluster_id: str                         # Cluster identifier
    number_of_logs: int                     # Logs in this batch
    processing_time_ms: float               # Total time
    cache_key: str                          # Cache lookup key
    source: str                             # "CACHE" or "SLM"
    slm_raw_output: str                     # Raw model output
    logs: List[LogTrace] {
      text: str                             # Original log
      template: str                         # Generated template
      source: str                           # "CACHE" or "SLM"
      level: str                            # INFO/WARN/ERROR
      event_type: str                       # AUTH/NETWORK/DB/SYSTEM/GENERIC
      masked: str                           # Dynamic parts replaced
    }
  }
}
```

---

## Tree Structure & Storage

### What Is The Tree?

The **Template Tree** is a hierarchical JSON structure that organizes all templates and logs processed by the system. It provides multiple levels of aggregation for easy navigation and analysis.

### Tree Hierarchy

```
ROOT (Template Tree)
  │
  ├─► Levels (by severity)
  │    │
  │    ├─► INFO (color: blue)
  │    │    │
  │    │    ├─► Event Types
  │    │    │    │
  │    │    │    ├─► "login" (example)
  │    │    │    │    │
  │    │    │    │    └─► Templates (sorted by frequency)
  │    │    │    │        │
  │    │    │    │        ├─► Template 1
  │    │    │    │        │    ├─ template_text
  │    │    │    │        │    ├─ count (in this run)
  │    │    │    │        │    ├─ global_count (all time)
  │    │    │    │        │    ├─ first_seen
  │    │    │    │        │    ├─ last_seen
  │    │    │    │        │    ├─ source ratios (cache% vs slm%)
  │    │    │    │        │    ├─ instances (sample logs)
  │    │    │    │        │    └─ [debug_info in debug mode]
  │    │    │    │        │
  │    │    │    │        └─► Template 2...
  │    │    │    │
  │    │    │    ├─► "database" (example)
  │    │    │    │    └─► Templates...
  │    │    │    │
  │    │    │    └─► other event types...
  │    │    │
  │    │    └─► other event types...
  │    │
  │    ├─► WARN (color: orange)
  │    │    └─► [similar structure]
  │    │
  │    └─► ERROR (color: red)
  │         └─► [similar structure]
  │
  ├─► generated_at (ISO timestamp)
  ├─► latest_batch_id (highest batch ID processed)
  ├─► show_current_batch (boolean flag)
  ├─► debug_mode (includes extra debug info)
  └─► total_logs (sum of all logs)
```

### Complete Tree Node Example

```json
{
  "generated_at": "2026-03-27T12:00:00Z",
  "latest_batch_id": 12,
  "show_current_batch": true,
  "debug_mode": false,
  "total_logs": 5,
  "levels": {
    "INFO": {
      "color": "blue",
      "event_types": {
        "login": {
          "templates": [
            {
              "template_text": "User <*> logged in from <*>",
              "count": 3,                              # In this run
              "global_count": 120,                     # All-time total
              "first_seen": "2026-03-20T09:00:00Z",   # First occurrence
              "last_seen": "2026-03-27T11:59:00Z",    # Most recent

              "source": {
                "cache": 2,                            # Times served from cache
                "slm": 1,                              # Times generated by SLM
                "cache_pct": 66.67,
                "slm_pct": 33.33
              },

              "current_batch_count": 2,               # In latest batch
              "highlight_current_batch": true,

              "instances": [                          # Sample log instances
                {
                  "original_log": "User 123 logged in from 10.0.0.1",
                  "source": "CACHE",                  # Where it came from
                  "batch_id": 12,
                  "cluster_id": "user <num> logged",
                  "masked": "user <*> logged in from <*>",
                  "in_current_batch": true
                },
                ...
              ],

              "instances_total": 3,                   # Total instances
              "instances_truncated": false,           # Limited to 25
              "omitted_instances": 0,

              "example_logs": [                       # Example lines
                "User 123 logged in from 10.0.0.1",
                "User 456 logged in from 10.0.0.2"
              ],

              "debug": {                              # Only in debug_mode
                "cluster_ids": ["user <num> logged"],
                "cache_hit": 2,
                "cache_miss": 1,
                "raw_slm_outputs": ["User <*> logged in from <*>"]
              }
            }
          ]
        },
        "database": {...},
        "request": {...}
      }
    },
    "WARN": {...},
    "ERROR": {...}
  }
}
```

### How Tree Is Built

The `build_template_tree()` function:

1. **Collects all logs** from the run trace
2. **Groups by level** (ERROR, WARN, INFO)
3. **Groups by event type** (within each level)
4. **Groups by template** (within each event type)
5. **Accumulates statistics**:
   - Count of logs matching this template
   - Source information (cache vs SLM)
   - First/last seen timestamps
   - Sample instances (up to limit)
6. **Sorts templates** by frequency (highest first)
7. **Highlights current batch** if enabled
8. **Includes debug info** if debug_mode is True

### Storage

The tree can be stored in multiple ways:

1. **In-Memory**: Always available via `pipeline.get_last_trace()`
2. **Database**: Can be saved to `tree_history` table for historical tracking
3. **JSON Export**: Can be written to file or sent via API

---

## Database Persistence

### Architecture

```
┌──────────────────────────────────────────────────┐
│  Application Layer                               │
│  (Pipeline, Cache, Registry)                     │
└────────────┬─────────────────────────────────────┘
             │
      ┌──────▼────────┐
      │  TemplateDB   │  Thread-safe wrapper
      │  (db.py)      │  with RLock
      └──────┬────────┘
             │
      ┌──────▼────────────────────────┐
      │  SQLite Database File         │
      │  (log_parser/data/templates.  │
      │   db)                         │
      └────────────────────────────────┘
```

### Initialization Flow

```python
# On first use:
db = TemplateDatabase("log_parser/data/templates.db")
  ├─ Create data directory if missing
  ├─ Create SQLite connection
  ├─ Initialize schema (CREATE TABLE IF NOT EXISTS)
  └─ Ready for operations

# Subsequent uses:
db = TemplateDatabase(...)
  └─ Reconnect to existing database
```

### Key Operations

**1. Cache Operations**

```python
# Store a template
db.cache_set(cache_key, template_text)
  └─ INSERT or UPDATE cache_entries

# Retrieve a template
template = db.cache_get(cache_key)
  └─ SELECT from cache_entries WHERE cache_key

# Get all cached entries
all_entries = db.get_all_cache_entries()
  └─ Returns {cache_key: template_text, ...}
```

**2. Stats Operations**

```python
# Record template usage
db.record_template_usage(template_text, source, example_log)
  └─ INSERT or UPDATE template_stats

# Retrieve stats
stats = db.get_template_stats()
  └─ SELECT * FROM template_stats
     Returns list of TemplateStats

# Get specific template
stat = db.get_template_stat(template_text)
  └─ SELECT WHERE template_text
```

**3. Tree History Operations**

```python
# Save tree snapshot
db.save_tree_history(tree_data_json, batch_id, total_logs)
  └─ INSERT INTO tree_history

# Get tree history
histories = db.get_tree_history(limit=10)
  └─ SELECT * FROM tree_history ORDER BY created_at DESC
```

**4. Example Logs Operations**

```python
# Store example log
db.add_example_log(template_text, log_text, level, event_type, source, batch_id)
  └─ INSERT INTO example_logs

# Get examples for template
examples = db.get_example_logs_for_template(template_text, limit=5)
  └─ SELECT * FROM example_logs WHERE template_text
```

### Data Synchronization

**Cache Synchronization**:

1. On startup, `TemplateCache` pre-loads all cache entries from DB
2. On each `set()`, writes to memory first, then to DB
3. DB write happens asynchronously to avoid blocking
4. Errors logged but don't block cache operation

**Registry Synchronization**:

1. On startup, `TemplateIntelligenceRegistry` loads all stats from DB
2. As templates are recorded, stats are updated in memory and DB
3. Timestamps automatically maintained by database triggers

### Concurrency

All database operations are protected by thread-safe locks:

```python
with self._lock:
    # Database operation
    conn = self._get_connection()
    cursor = conn.cursor()
    cursor.execute(...)
    conn.commit()
```

This ensures consistency when multiple threads access the database.

---

## How It Works - Detailed

### End-to-End Processing Example

Let's trace a complete request through the system:

**Input**: 3 log lines

```
logs = [
  "User 123 logged in from 10.0.0.1",
  "User 456 logged in from 10.0.0.2",
  "Database query timed out after 5000ms"
]
```

**Step 1: Clustering**

```
Clusterer.cluster(logs):

Log 1: "User 123 logged in from 10.0.0.1"
  ├─ Normalize: "user <num> logged in from <ip>"
  ├─ Signature: "user <num> logged" (first 3 tokens)
  └─ Cluster ID: "user <num> logged"

Log 2: "User 456 logged in from 10.0.0.2"
  ├─ Normalize: "user <num> logged in from <ip>"
  ├─ Signature: "user <num> logged"
  └─ Same cluster

Log 3: "Database query timed out after 5000ms"
  ├─ Normalize: "database query timed out after <num>ms"
  ├─ Signature: "database query timed"
  └─ Different cluster ID: "database query timed"

Result:
  Cluster 1: {id: "user <num> logged", indices: [0,1], logs: [log1, log2]}
  Cluster 2: {id: "database query timed", indices: [2], logs: [log3]}
```

**Step 2: Batching & Cache Lookup**

```
Cluster 1 (batch_size=2):
  batch_id = 1
  batch_logs = [log1, log2]
  cache_key = SHA256("user <num> logged" + "||" + log1 + "\n" + log2)
            = "abc123def456..."

  Cache.get("abc123def456...") = None (MISS)

Cluster 2 (batch_size=2):
  batch_id = 2
  batch_logs = [log3]
  cache_key = SHA256("database query timed" + "||" + log3)
            = "xyz789abc000..."

  Cache.get("xyz789abc000...") = None (MISS)
```

**Step 3: SLM Parsing**

```
Batch 1:
  Prompt = """
  You are a deterministic log template extractor...
  Logs:
  - User 123 logged in from 10.0.0.1
  - User 456 logged in from 10.0.0.2
  Template:
  """

  Model output: "User <*> logged in from <*>"
  Post-process: "User <*> logged in from <*>"
  Final template: "User <*> logged in from <*>"

Batch 2:
  Prompt = """
  You are a deterministic log template extractor...
  Logs:
  - Database query timed out after 5000ms
  Template:
  """

  Model output: "Database query timed out after <*>ms"
  Post-process: "Database query timed out after <*>ms"
  Final template: "Database query timed out after <*>ms"
```

**Step 4: Cache & Registry Update**

```
For Batch 1:
  Cache.set("abc123def456...", "User <*> logged in from <*>")
    └─ Stored in memory + SQLite

  Registry.record(
    template="User <*> logged in from <*>",
    source="SLM",
    example_log="User 123 logged in from 10.0.0.1"
  )

For Batch 2:
  Cache.set("xyz789abc000...", "Database query timed out after <*>ms")
  Registry.record(
    template="Database query timed out after <*>ms",
    source="SLM",
    example_log="Database query timed out after 5000ms"
  )
```

**Step 5: Log Trace Creation**

```
For each log, create LogTrace:

Log 1:
  LogTrace {
    text: "User 123 logged in from 10.0.0.1",
    template: "User <*> logged in from <*>",
    source: "SLM",
    level: "INFO" (contains "logged in"),
    event_type: "AUTH" (contains "logged in"),
    masked: "User <*> logged in from <*>"
  }

Log 2: (same template)
  LogTrace {...}

Log 3:
  LogTrace {
    text: "Database query timed out after 5000ms",
    template: "Database query timed out after <*>ms",
    source: "SLM",
    level: "ERROR" (contains "timed"),
    event_type: "DB" (contains "query"),
    masked: "Database query timed out after <*>ms"
  }
```

**Step 6: Tree Building**

```
build_template_tree(trace, stats):

Current batch includes:
  - INFO/AUTH: "User <*> logged in from <*>" (count: 2)
  - ERROR/DB: "Database query timed out after <*>ms" (count: 1)

Global stats (from database):
  - "User <*> logged in from <*>": 120 total uses
  - "Database query timed out after <*>ms": 45 total uses

Result Tree:
{
  "generated_at": "2026-03-28T10:30:00Z",
  "latest_batch_id": 2,
  "levels": {
    "INFO": {
      "color": "blue",
      "event_types": {
        "auth": {
          "templates": [
            {
              "template_text": "User <*> logged in from <*>",
              "count": 2,
              "global_count": 120,
              "instances": [log1_trace, log2_trace],
              ...
            }
          ]
        }
      }
    },
    "ERROR": {
      "color": "red",
      "event_types": {
        "database": {
          "templates": [
            {
              "template_text": "Database query timed out after <*>ms",
              "count": 1,
              "global_count": 45,
              "instances": [log3_trace],
              ...
            }
          ]
        }
      }
    }
  }
}
```

**Step 7: Output**

```
Return templates (one per input log):
[
  "User <*> logged in from <*>",
  "User <*> logged in from <*>",
  "Database query timed out after <*>ms"
]
```

---

## API Reference

### REST API (FastAPI)

All endpoints return JSON and can be accessed at `http://{api_host}:{api_port}`

#### 1. **GET /health**

Health check endpoint.

**Response**:

```json
{
	"status": "ok",
	"model": "distilgpt2",
	"log_file": "logs/system.log"
}
```

#### 2. **POST /parse**

Parse logs and generate templates.

**Request Body**:

```json
{
	"logs": [
		"User 123 logged in from 10.0.0.1",
		"User 456 logged in from 10.0.0.2"
	]
}
```

**Query Parameters**:

- `debug` (boolean): Include detailed trace in response (default: false)

**Response**:

```json
{
  "templates": [
    "User <*> logged in from <*>",
    "User <*> logged in from <*>"
  ],
  "trace": {
    "total_logs": 2,
    "batch_count": 1,
    "template_count": 1,
    "distribution": {
      "User <*> logged in from <*>": 2
    },
    "batches": [...]  // Only if debug=true
  }
}
```

#### 3. **GET /batches/latest**

Get detailed trace of the most recent batch processing.

**Response**:

```json
{
  "total_logs": 5,
  "batch_count": 2,
  "template_count": 3,
  "distribution": {...},
  "batches": [
    {
      "batch_id": 1,
      "cluster_id": "user <num> logged",
      "number_of_logs": 2,
      "processing_time_ms": 1234.567,
      "cache_key": "abc123...",
      "source": "SLM",
      "slm_raw_output": "User <*> logged in from <*>",
      "logs": [...]
    }
  ]
}
```

#### 4. **GET /templates/stats**

Get global template statistics.

**Response**:

```json
[
  {
    "template_text": "User <*> logged in from <*>",
    "usage_count": 120,
    "first_seen": "2026-03-20T09:00:00Z",
    "last_used": "2026-03-28T10:30:00Z",
    "example_log": "User 123 logged in from 10.0.0.1",
    "source_ratio": {
      "cache_pct": 75.0,
      "slm_pct": 25.0
    }
  },
  ...
]
```

#### 5. **GET /templates/tree**

Get hierarchical template tree (main visualization data).

**Query Parameters**:

- `show_current_batch` (boolean): Highlight templates from latest batch (default: true)
- `debug` (boolean): Include debug info per template (default: false)
- `instance_limit` (integer): Max sample instances per template (default: 25)

**Response**: Complete template tree structure (see [Tree Structure](#tree-structure--storage))

#### 6. **GET /templates/tree/example**

Get example tree structure (for UI development).

**Response**: Pre-built tree example from `examples/tree_example.json`

#### 7. **POST /classify**

Placeholder endpoint for future template classification.

**Request Body**:

```json
{
	"template": "User <*> logged in from <*>"
}
```

**Response**:

```json
{
	"label": "authentication"
}
```

---

## UI Dashboard

### Overview

The Gradio-based web interface provides interactive log parsing and visualization.

**Access**: `http://localhost:7860` (or configured UI port)

### Features

#### 1. **Log Input**

- Multi-line text area for log input
- Real-time processing as logs are entered
- Supports copy-paste of large log files

#### 2. **Processing Options**

- **Show Current Batch**: Highlight templates from the latest batch
- **Debug Mode**: Show cluster IDs, cache hits/misses, raw SLM output
- **Instance Limit**: Control number of sample log instances displayed (1-500)

#### 3. **Output Tabs**

**Tab 1: Parsed Templates**

- Display generated templates for each input log
- Shows one template per input line
- Highlights common templates

**Tab 2: Template Viewer**

- Markdown-formatted list of unique templates
- Shows usage statistics for each:
  - Total usage count
  - Last used timestamp
  - Example log
  - Cache vs SLM contribution percentages

**Tab 3: Batch Analysis**

- Detailed breakdown of batch processing
- For each batch:
  - Batch ID
  - Cluster ID
  - Number of logs
  - Processing source (CACHE/SLM)
  - Processing time
  - Template distribution within batch

**Tab 4: Tree Visualization**

- Interactive HTML rendering of template tree
- Color-coded by log level:
  - Blue = INFO
  - Orange = WARN
  - Red = ERROR
- Grouped by event type
- Sortable by frequency
- Current batch highlighting

#### 4. **Real-Time Updates**

- Processing status shown during execution
- Error messages displayed if parsing fails
- Fallback to heuristic templates if model unavailable

---

## Configuration

### Configuration File

**Location**: `log_parser/configs/config.yaml`

### Parameters

```yaml
model:
  name_or_path: "distilgpt2" # HuggingFace model identifier
  max_new_tokens: 64 # Max tokens to generate

pipeline:
  batch_size: 16 # Logs per batch
  min_cluster_tokens: 3 # Min tokens for cluster signature

api:
  host: "127.0.0.1" # API server host
  port: 8000 # API server port

observability:
  log_file_path: "logs/system.log" # Structured log output

ui:
  port: 7860 # Gradio UI port
```

### Configuration Loading

```python
from log_parser.config import load_config

config = load_config("log_parser/configs/config.yaml")
# Returns AppConfig object with all parameters
```

### Model Selection

Any HuggingFace-compatible causal language model can be used:

**Recommended Models**:

- `distilgpt2` (Small, ~82MB)
- `gpt2` (Medium, ~548MB)
- `microsoft/phi-2` (Larger, ~5.8GB)
- `TinyLlama/TinyLlama-1.1B` (~1.1GB)

**Selection Criteria**:

- **Speed**: Smaller models faster but less accurate
- **Accuracy**: Larger models more accurate but slower/more memory
- **Memory**: Consider available GPU/CPU memory

---

## Usage Examples

### 1. CLI Usage

**Basic parsing**:

```bash
python main.py --mode cli \
  --logs "User 123 logged in" "User 456 logged in" "Error: connection timeout"
```

**With custom config**:

```bash
python main.py --mode cli \
  --config custom_config.yaml \
  --logs "Log 1" "Log 2"
```

**Output**:

```
User <*> logged in
User <*> logged in
Error: connection <*>
```

### 2. API Server

**Start server**:

```bash
python main.py --mode api --config log_parser/configs/config.yaml
```

**Parse logs via curl**:

```bash
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      "User 123 logged in from 10.0.0.1",
      "User 456 logged in from 10.0.0.2"
    ]
  }'
```

**Get template tree**:

```bash
curl -X GET "http://localhost:8000/templates/tree?debug=true&show_current_batch=true"
```

**Get statistics**:

```bash
curl -X GET http://localhost:8000/templates/stats
```

### 3. Web UI

**Start UI**:

```bash
python main.py --mode ui
```

**Use in browser**:

1. Navigate to `http://localhost:7860`
2. Enter logs in the text area
3. Adjust options (debug mode, instance limit, etc.)
4. View results in different tabs

### 4. Programmatic Usage

**Python Integration**:

```python
from log_parser.factory import build_pipeline

# Initialize
pipeline, config = build_pipeline("log_parser/configs/config.yaml")

# Parse logs
logs = ["User 123 logged in", "User 456 logged in"]
templates = pipeline.run(logs)

# Access trace
trace = pipeline.get_last_trace()
print(f"Processed {trace.to_dict()['total_logs']} logs")

# Access statistics
stats = pipeline.get_template_stats()
for stat in stats:
    print(f"Template: {stat['template_text']}")
    print(f"  Usage: {stat['usage_count']}")
    print(f"  Cache: {stat['source_ratio']['cache_pct']}%")
```

### 5. Database Management

**Access database directly**:

```python
from log_parser.pipeline.db import TemplateDatabase

db = TemplateDatabase("log_parser/data/templates.db")

# Get all cached templates
all_cache = db.get_all_cache_entries()

# Get template stats
stats = db.get_template_stats()

# Export tree history
history = db.get_tree_history(limit=10)

# Query examples
examples = db.get_example_logs_for_template("User <*> logged in from <*>")
```

---

## Observability & Logging

### Structured Logging

All operations produce structured JSON logs written to `logs/system.log`.

**Log Levels**:

- INFO: Normal operation, batch start/end
- DEBUG: Detailed processing steps
- WARNING: Recoverable issues (model errors)
- ERROR: Critical failures

### Emitted Events

The system emits events for major operations:

**Batch Processing Event**:

```json
{
	"timestamp": "2026-03-28T10:30:00.123Z",
	"level": "INFO",
	"event": "batch_processed",
	"batch_id": 1,
	"cluster_id": "user <num> logged",
	"logs_count": 2,
	"source": "SLM",
	"processing_time_ms": 1234.567,
	"cache_key": "abc123def456...",
	"template": "User <*> logged in from <*>"
}
```

**Template Cache Event**:

```json
{
	"timestamp": "2026-03-28T10:30:00.456Z",
	"level": "DEBUG",
	"event": "template_cached",
	"cache_key": "abc123...",
	"template": "User <*> logged in",
	"hit_count": 5
}
```

**Error Event**:

```json
{
	"timestamp": "2026-03-28T10:30:00.789Z",
	"level": "WARNING",
	"event": "model_inference_error",
	"error": "Model not found",
	"fallback": "heuristic_template"
}
```

### Performance Metrics

The system tracks:

- **Batch processing time**: End-to-end time per batch
- **Cache hit rate**: % of templates served from cache
- **Template generation time**: Time spent in SLM inference
- **Database operations**: Time spent in persistence

These are automatically included in the trace data.

---

## Summary

**LogBatcher** is a comprehensive log intelligence platform that:

1. **Clusters** similar logs efficiently
2. **Generates** templates using local SLM models
3. **Caches** results to avoid redundant processing
4. **Persists** all data in a relational database
5. **Organizes** results in a hierarchical tree structure
6. **Observes** all operations with structured logging
7. **Provides** multiple interfaces (CLI, API, UI)
8. **Tracks** statistics for performance analysis

The architecture emphasizes **modularity**, **determinism**, **observability**, and **fault tolerance**, making it suitable for production use in log analytics pipelines.
