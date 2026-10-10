# AI Document Q&A and Model Playground

<div align="center">

![LangChain](https://img.shields.io/badge/LangChain-LCEL-blue.svg?style=for-the-badge&logo=langchain)
![LangGraph](https://img.shields.io/badge/LangGraph-4--Agent--Workflow-orange.svg?style=for-the-badge&logo=python)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector--Database-red.svg?style=for-the-badge&logo=qdrant)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg?style=for-the-badge&logo=react)
![Docker](https://img.shields.io/badge/Docker-Compose--Ready-2496ED.svg?style=for-the-badge&logo=docker)

**A full-stack document Q&A API and browser-based model playground**

[Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Testing](#-testing- suite)

</div>

---

## 🌟 Overview

This repository contains a React model playground and a FastAPI document Q&A service. The backend uses a compiled LangGraph workflow, LangChain's LCEL for Groq chat calls, Qdrant for document storage/search, and SQLAlchemy for application records and telemetry.

It is a prototype, not a production-ready enterprise platform. The browser playground calls selected providers directly; the backend RAG endpoint currently supports Groq as its live model provider and otherwise returns retrieved passages without claiming they are generated answers.

---

## 🔥 Key Features

### 🤖 1. LangGraph Workflow
The backend compiles four Python processing steps into a sequential **LangGraph `StateGraph`**:
* **Document processing** — Validates and sanitizes the query and splits multi-question inputs.
* **Retrieval** — Searches Qdrant, with an in-memory lexical fallback.
* **Reasoning** — Uses a LangChain LCEL chain (`ChatPromptTemplate | ChatOpenAI | StrOutputParser`) for Groq. Without a live model response, it returns retrieved passages with citations instead of canned answers.
* **Verification** — Applies a heuristic context-overlap confidence check; this is not an independent model-based fact checker.

### 🔍 2. Document ingestion and retrieval
* **Multi-Format Ingestion:** Parsers for **PDF, DOCX, TXT, and Markdown**.
* **Chunking:** Splits ingested content into chunks and stores source metadata.
* **Embeddings:** Uses FastEmbed's `sentence-transformers/all-MiniLM-L6-v2` CPU model for 384-dimensional semantic embeddings. The model downloads on first use.
* **Hybrid search:** Combines Qdrant semantic similarity with BM25-style keyword relevance. The current implementation loads document text into memory for keyword ranking, so its corpus size is limited by backend memory.
* **Existing Qdrant data:** Startup copies chunks from the legacy `enterprise_documents` collection into `enterprise_documents_v2`, re-embedding them while preserving the legacy collection. Existing data remains available if migration is interrupted.
* **Citations:** Responses include retrieved source filenames and context snippets.

### 🛡️ 3. Pure Python Security Guardrails
* **PII Masking:** Query sanitization masks detected emails, phone numbers, and SSNs.
* **Prompt Injection Detection:** Checks query text against configured injection patterns.
* **CORS & HTTP Security Headers:** Enforces `nosniff`, `DENY` framing, and restricted origin policies.

### 📊 4. Telemetry & Admin Dashboard
* **Query Latency Tracking:** Records total workflow latency.
* **Token and cost metrics:** Estimates based on text length; these are not provider-reported token usage or billing data.
* **Confidence metrics:** Tracks heuristic confidence scores and flagged responses.
* **SQL Storage:** Persists users, chat sessions, and evaluation logs (PostgreSQL in Docker; SQLite by default for local setup).

---

## 🏗️ Architecture

```mermaid
flowchart TD
    User([👤 User / Developer]) --> UI[🌐 React AI Playground UI]
    UI --> REST[⚡ FastAPI REST API Gateway]
    
    subgraph Guardrails ["🛡️ Enterprise Security Layer"]
        REST --> G1[PII Sanitizer & Masker]
        G1 --> G2[Prompt Injection Detector]
    end

    subgraph LangGraph ["🤖 Compiled LangGraph StateGraph"]
        G2 --> A1[Agent 1: Doc Processing Agent]
        A1 --> A2[Agent 2: Retriever Agent]
        A2 <--> Qdrant[(🔴 Qdrant Vector Store)]
        A2 --> A3[Agent 3: Reasoning Agent]
        A3 <--> Groq[☁️ Groq via LangChain LCEL]
        A3 --> A4[Agent 4: Verification Agent]
    end

    A4 --> Audit[(🐘 PostgreSQL Telemetry DB)]
    A4 --> Response[✨ Grounded Response + Citations + Telemetry]
    Response --> UI
```

The browser playground is a separate client-side app. Its chain visualizer is illustrative; the backend RAG endpoint is the part that executes the LangGraph workflow and LangChain chain.

---

## ⚡ Quick Start

### Option A: Docker Compose (Recommended)
Launch the full stack (Frontend + Backend + PostgreSQL + Qdrant) in one command:

```bash
docker-compose up --build
```
* **Frontend Playground:** `http://localhost:3000`
* **FastAPI Backend:** `http://localhost:8000`
* **Interactive Swagger Docs:** `http://localhost:8000/docs`
* **Qdrant Vector Console:** `http://localhost:6333`

Set a Groq key in the playground settings for live model responses. Without one, the backend returns retrieved passages rather than generating a synthesized answer. The first document indexing run downloads the embedding model and requires network access. When changing `EMBEDDING_MODEL`, configure a new Qdrant collection and re-index/migrate documents; vectors from different models must not share a collection.

---

### Option B: Local Manual Setup

#### 1. Backend (`apps/enterprise-api`)
```bash
cd apps/enterprise-api

# Install dependencies
pip install -e .

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend (`apps/free-ai-playground`)
```bash
cd apps/free-ai-playground

# Install dependencies
npm install

# Start Vite React development server
npm run dev
```

---

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | `GET` | System health check & version info |
| `POST /api/v1/chat` | `POST` | Execute 4-Agent RAG Pipeline with query payload |
| `POST /api/v1/documents/upload` | `POST` | Upload & chunk document into Qdrant vector store |
| `GET /api/v1/documents` | `GET` | List all indexed enterprise documents |
| `DELETE /api/v1/documents/{id}` | `DELETE` | Delete document & remove chunks from vector store |
| `GET /api/v1/metrics` | `GET` | Fetch telemetry, latency, token metrics, and agent logs |
| `GET /api/v1/admin/stats` | `GET` | Admin dashboard overview statistics |

---

## 🧪 Testing & Verification

Run the full automated platform and bug regression test suites:

```bash
cd apps/enterprise-api

# Backend Test Suite
python -c "import sys; sys.path.insert(0, '.'); import unittest; unittest.main(module='tests.run_tests')"

# Bug Fix & RAG Retrieval Regression Suite (5 Tests)
python -c "import sys; sys.path.insert(0, '.'); import unittest; unittest.main(module='tests.test_bugs_regression')"
```

---

## 👨‍💻 Author

**Abhishek**
* **GitHub:** [@i-abhishek-04](https://github.com/i-abhishek-04)
* **Project:** AI Document Q&A and Model Playground

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
