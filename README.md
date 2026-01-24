# SLM-Based Resource Efficient Log Analysis System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat&logo=python)
![AI](https://img.shields.io/badge/AI-Hugging%20Face-yellow?style=flat&logo=huggingface)
![Architecture](https://img.shields.io/badge/Architecture-RAG%20%26%20SLM-green)
![Status](https://img.shields.io/badge/Status-Prototype-orange)

## Abstract
This project presents a conceptual architecture for a Resource-Efficient AIOps Pipeline designed to analyze high-volume system logs using Small Language Models (SLMs).

While Large Language Models (LLMs) offer strong performance in log analysis, they often suffer from high latency and operational costs in online scenarios. To address this, this system proposes an end-to-end pipeline that integrates Micro-Batching, Retrieval-Augmented Generation (RAG), and Predictive Maintenance (PdM) to provide real-time anomaly detection and root cause analysis (RCA) without the heavy computational burden of giant models.

## Key Features

Based on the systematic review and architectural proposal:

* **SLM-First Approach:** Optimized to run on Small Language Models (e.g., TinyLlama, Phi-2) for low-latency inference rather than relying solely on costly LLM APIs.
* **Micro-Batch Processing:** Processes logs in time-windows (e.g., 1 minute) or line-counts (e.g., 50 lines) to reduce the number of model calls and amortize costs.
* **RAG-Based Event Memory:** Utilizes a vector database to retrieve historical incident records and "similar past solutions" as context for the current analysis.
* **Evidence-Based RCA:** Reduces AI hallucinations by grounding Root Cause Analysis (RCA) in retrieved log evidence and system metadata.
* **Predictive Maintenance (PdM):** Includes an early warning module to predict potential system crashes based on causal insights and time-series indicators.

## System Architecture

The pipeline consists of four main modules:

1.  **Data Ingestion & Preprocessing:** Streaming logs collection and template parsing.
2.  **Event Memory & Retrieval:** Embedding generation and vector search (RAG).
3.  **Analysis & Reasoning:** Anomaly detection and state summarization.
4.  **Output & Interaction:** RCA reporting and Natural Language Query Interface for operators.

> ![System Architecture](architecture.png)
> *(Please upload the architecture diagram from your paper here)*

## Tech Stack

* **Language:** Python
* **AI & NLP:** Hugging Face Transformers, PyTorch, LangChain
* **Data Processing:** Pandas, NumPy
* **Vector Database:** FAISS (Planned integration for RAG)
* **Techniques:** Prompt Engineering, Parameter-Efficient Fine-Tuning (PEFT), Cosine Similarity

## Operational Workflow (Scenario)

The system follows a structured data flow to ensure context-aware analysis:

| Stage | Input | Expected Output |
| :--- | :--- | :--- |
| **1. Micro-Batching** | Raw log stream (e.g., 1 min window) | Batch ID + Raw Lines |
| **2. Parsing** | Raw logs within the batch | Log Templates + Parameters |
| **3. Embedding** | Log Templates | Vector Representations |
| **4. Retrieval (RAG)** | Current Vector | Similar Historical Incidents & Solutions |
| **5. Anomaly Detection** | Template Sequence + Similarity Score | Anomaly Label (e.g., High Deviation) |
| **6. Summarization** | Evidence Lines + Metadata | Concise Event Summary (e.g., "DB Timeout Spike") |
| **7. RCA Support** | Summary + Retrieved Context | Hypothesis List (e.g., "Check DB Locks") |
| **8. Early Warning** | Time-series History | Risk Alert (e.g., "Crash risk in 2 hours") |

## Reference

This project is part of a senior capstone study titled:
> "SLM-Based Resource Efficient Log Analysis System: Systematic Review and End-to-End SLM-Based Architecture Proposal".

---
*Author: [Your Name]*
*Contact: [Your Email/LinkedIn]*
