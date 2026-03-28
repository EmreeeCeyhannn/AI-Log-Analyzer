You are a senior ML engineer, backend architect, and observability expert.

I have refactored a LogBatcher-based project, but I am NOT confident it meets production requirements.

Your job is to:

1. Audit the current system
2. Identify if it truly:
   - Uses SLM instead of LLM
   - Avoids external API calls
   - Properly implements clustering, caching, batching

3. Then IMPROVE and EXTEND it into a fully observable, debuggable production system

---

# 🔍 PART 1 — SYSTEM AUDIT (VERY IMPORTANT)

First, analyze the codebase and clearly answer:

### 1. Model Usage

- Which model is used?
- Is it:
  - Local SLM (correct) ✅
  - External API (wrong) ❌

- If API:
  - Which provider?
  - Is it free/paid?

---

### 2. Parsing Source

For each parsing operation:

- Is it using:
  - Cached template?
  - SLM inference?

---

### 3. Clustering

- What clustering algorithm is used?
- How are logs grouped?
- Is it deterministic?

---

### 4. Template Storage

- How are templates stored?
  - Dictionary?
  - File?
  - DB?

- What is the structure?

---

### 5. Output Consistency

- Are templates stable?
- Any randomness?

---

Provide a clear technical report before making changes.

---

# 🚀 PART 2 — ADD FULL OBSERVABILITY SYSTEM

You MUST implement a detailed logging + tracing system.

---

## 🧠 Logging Requirements

For EVERY batch:

Log the following:

- batch_id
- number_of_logs
- cluster_id
- processing_time

For EACH log:

- original_log
- assigned_template
- source:
  - "CACHE"
  - "SLM"

- log_level:
  - INFO / ERROR / WARN (extract from log)

- event_type (if detectable)

---

## 🧾 Example Log Output

```json
{
	"batch_id": 12,
	"cluster_id": 3,
	"logs": [
		{
			"text": "User 123 logged in",
			"template": "User <*> logged in",
			"source": "SLM",
			"level": "INFO"
		},
		{
			"text": "User 456 logged in",
			"template": "User <*> logged in",
			"source": "CACHE",
			"level": "INFO"
		}
	]
}
```

---

## ⚙️ Logging Implementation

- Use structured logging (JSON)
- Write to:
  - file (logs/system.log)
  - console

---

# 🧱 PART 3 — TEMPLATE INTELLIGENCE LAYER

Track templates globally:

For each template store:

- template_text
- usage_count
- last_used
- source_ratio:
  - % from cache
  - % from SLM

---

# 📊 PART 4 — UI REQUIREMENTS (VERY IMPORTANT)

Build a UI (Gradio or simple dashboard) with:

---

## 🖥️ 1. Template Viewer

Show:

- Template list
- Count per template
- Example logs

---

## 📊 2. Batch Analysis View

For each batch:

Show:

- total logs
- number of templates
- distribution:

Example:

```text
Template A → 10 logs
Template B → 5 logs
Template C → 2 logs
```

---

## 🔍 3. Source Visualization

For each template show:

- % from CACHE
- % from SLM

---

## 🧠 4. Log Structure Extraction

For each log display:

- static parts:
  - INFO / ERROR / WARN
  - event keyword

- dynamic parts masked

---

## 🎯 5. Debug Mode

Enable a toggle:

When ON:

- Show:
  - clustering result
  - cache hit/miss
  - SLM raw output

---

# ⚠️ PART 5 — STRICT REQUIREMENTS

- NO external LLM APIs
- MUST use local SLM
- deterministic outputs (temperature=0)
- batch processing must remain
- cache must be used properly

---

# 🎯 FINAL OUTPUT

You must deliver:

1. Audit report (what is wrong now)
2. Refactored code
3. Logging system
4. UI dashboard
5. Example outputs
6. Instructions to run

---

# 💡 IMPORTANT

This is NOT just a refactor.

This is:
→ turning the system into a debuggable, production-grade log intelligence platform

Focus on visibility, traceability, and control.
