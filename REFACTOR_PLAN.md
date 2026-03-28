# 🚀 LogBatcher → SLM-Based Production System Refactor Plan

## 🎯 Objective

Refactor the existing LogBatcher project into a production-ready system by:

- Replacing LLM-based parsing with a fine-tuned SLM
- Keeping core pipeline logic (clustering, caching, batching)
- Introducing modular architecture
- Adding API and UI layers

---

## 🧠 Current System Overview

The existing system:

- Uses LLMs for log template extraction
- Groups logs via clustering
- Uses cache to reduce repeated parsing
- Processes logs in batches

---

## 🔧 Target Architecture

```
log_parser/
│
├── pipeline/
│   ├── pipeline.py
│   ├── clustering.py
│   ├── cache.py
│   ├── parser.py
│   └── postprocess.py
│
├── models/
│   └── slm_model.py
│
├── api/
│   └── fastapi_app.py
│
├── ui/
│   └── app.py
│
├── configs/
│   └── config.yaml
│
└── main.py
```

---

## 🔁 Key Changes

### 1. LLM → SLM

Replace:

- External LLM API calls

With:

- Local fine-tuned SLM

---

### 2. Parser Abstraction

Introduce:

```python
class BaseParser:
    def parse(self, logs):
        pass
```

```python
class SLMParser(BaseParser):
    def parse(self, logs):
        pass
```

---

### 3. Pipeline Refactor

Create:

```python
class LogPipeline:
    def run(self, logs):
        pass
```

Flow:

1. Clustering
2. Cache lookup
3. SLM parsing
4. Cache store
5. Output

---

### 4. API Layer

Using FastAPI:

Endpoints:

- `/parse`
- `/health`

---

### 5. UI Layer

Simple interface:

- Input logs
- Show parsed templates

---

## ⚠️ Constraints

- Must preserve batching logic
- Must preserve cache behavior
- Output format must remain consistent
- No external LLM APIs

---

## 🧪 Future Extensions

- Template classification (error detection)
- Semantic cache (vector DB)
- Online learning

---

## ✅ Expected Outcome

A clean, modular, production-ready system that:

- Uses SLM for parsing
- Is scalable and reusable
- Can be deployed as a service
