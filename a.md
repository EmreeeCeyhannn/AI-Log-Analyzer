You are a senior machine learning engineer and backend architect.

I have an open-source project (LogBatcher) that performs log parsing using LLMs. I want you to refactor and redesign this project into a production-ready, modular system with the following requirements:

## 🎯 Goal

Transform the existing codebase into a reusable, scalable log parsing system that:

* Replaces LLM-based parsing with a fine-tuned SLM (small language model)
* Keeps the existing pipeline logic (clustering, batching, caching)
* Adds a clean architecture
* Provides an API and simple UI for usage

---

## 🧱 Requirements

### 1. Architecture Refactor

Restructure the project into a modular architecture:

* pipeline/

  * pipeline.py (main orchestration)
  * clustering.py
  * cache.py
  * parser.py (IMPORTANT: abstraction layer)
  * postprocess.py

* models/

  * slm_model.py (wraps inference)

* api/

  * fastapi_app.py

* ui/

  * simple frontend (Gradio or minimal web UI)

* configs/

  * config.yaml

* main.py

---

### 2. Replace LLM with SLM

The current system uses LLM calls like:
call_llm(batch_logs)

You must:

* Remove all LLM dependencies
* Introduce a parser abstraction:

class BaseParser:
def parse(self, logs: List[str]) -> str

* Implement:

class SLMParser(BaseParser)

* The parser should:

  * Accept batch logs
  * Format them into a prompt
  * Call a local fine-tuned model
  * Return a structured log template

---

### 3. Keep Core Logic

Do NOT remove:

* Clustering logic
* Cache mechanism
* Batch processing

But:

* Clean and modularize them
* Make them reusable classes

---

### 4. Pipeline Design

Create a pipeline class:

class LogPipeline:
def run(logs: List[str]) -> List[str]

Steps:

1. Cluster logs
2. Check cache
3. Parse with SLM if needed
4. Store in cache
5. Return templates

---

### 5. API Layer

Build a FastAPI service:

Endpoints:

* POST /parse
  Input: list of logs
  Output: templates

* POST /classify (optional future)
  Input: template
  Output: error / normal

---

### 6. UI (Simple)

Add a simple UI:

* Use Gradio or minimal HTML frontend
* Input: logs
* Output: parsed templates

---

### 7. SLM Integration

Create a model wrapper:

class SLMModel:
def generate(prompt: str) -> str

Assume:

* Model is local (HuggingFace compatible)
* Deterministic output (temperature=0)

---

### 8. Output Format

Ensure parser outputs consistent templates like:

User <*> logged in from <*>

---

### 9. Deliverables

Provide:

1. Full refactored folder structure
2. Clean, production-ready code
3. Comments explaining each module
4. Example usage
5. API example request/response
6. Instructions to run locally

---

## ⚠️ Important Constraints

* Do NOT keep any LLM API calls
* Do NOT simplify logic too much
* Keep batching behavior
* Ensure deterministic outputs
* Make the system extensible

---

## 🎯 Final Goal

A production-ready log parsing system using:

* SLM instead of LLM
* Clean modular architecture
* API + UI support

Think like you're building a real SaaS backend.

Now refactor the project accordingly.
