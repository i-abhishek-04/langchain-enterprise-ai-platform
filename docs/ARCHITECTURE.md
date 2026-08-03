# 🏛️ Enterprise AI Engineering Platform Architecture

This document provides a comprehensive technical overview of the **LangChain Enterprise AI Engineering Platform**.

---

## 📐 High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        ReactUI["React + Vite Frontend (apps/free-ai-playground)"]
    end

    subgraph API ["FastAPI Engine (apps/enterprise-api)"]
        Router["API Router (/api/v1)"]
        Auth["JWT Auth & Security"]
        Guard["Guardrails Middleware (PII, Injections)"]
        Graph["LangGraph 4-Agent Orchestrator"]
        Ingest["Document Processing & Chunking"]
    end

    subgraph Data ["Data & Vector Layer"]
        Qdrant[("Qdrant Vector Database (Port 6333)")]
        Postgres[("PostgreSQL Database (Port 5432)")]
    end

    subgraph AI ["Free LLM Providers"]
        Groq["Groq Cloud (Llama 3.3 70B, DeepSeek R1)"]
        Gemini["Google Gemini 2.0 Flash"]
        OpenRouter["OpenRouter Free Tier"]
        Ollama["Local Ollama (localhost:11434)"]
    end

    ReactUI <-->|REST API / JSON| Router
    Router --> Auth
    Router --> Guard
    Guard --> Graph
    Ingest --> Qdrant
    Graph -->|Similarity Search| Qdrant
    Graph -->|Free LLM Inference| Groq & Gemini & OpenRouter & Ollama
    Router -->|Persist Logs, History & Metrics| Postgres
```

---

## 🤖 Phase 2: LangGraph 4-Agent Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Agent1 as DocProc Agent
    participant Agent2 as Retriever Agent
    participant Agent3 as Reasoning Agent
    participant Agent4 as Verification Agent
    participant Qdrant as Qdrant Vector DB
    participant LLM as Free LLM Engine

    User->>Agent1: Submit Query / Context
    Agent1->>Agent1: Validate & Mask PII & Detect Prompt Injections
    Agent1->>Agent2: Forward Sanitized Query
    Agent2->>Qdrant: Vector Similarity Search
    Qdrant-->>Agent2: Return Top-K Chunks
    Agent2->>Agent3: Context + Query Payload
    Agent3->>LLM: Constrained Generation Request
    LLM-->>Agent3: Draft Response Text
    Agent3->>Agent4: Draft Response + Context
    Agent4->>Agent4: Check Faithfulness & Hallucination Score
    alt Confidence Score >= 0.65
        Agent4-->>User: Return Verified Answer + Citations
    else Confidence Score < 0.65
        Agent4-->>User: Return "I don't have enough information."
    end
```

---

## 📁 Repository Folder Structure

```txt
langchain/
├── apps/
│   ├── enterprise-api/            # FastAPI Backend Application
│   │   ├── app/
│   │   │   ├── api/               # REST API Routers (/documents, /chat, /history, /metrics, /auth)
│   │   │   ├── agents/            # LangGraph 4-Agent Multi-Agent Workflow
│   │   │   ├── core/              # Security, JWT, App Config
│   │   │   ├── db/                # SQLAlchemy Models & Session
│   │   │   ├── guardrails/        # Injection Detection, PII Masking, Context Validation
│   │   │   ├── rag/               # Qdrant Vector Store & Ingestion Pipeline (PDF, DOCX, TXT, MD)
│   │   │   └── main.py            # FastAPI Entry Point
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── free-ai-playground/        # React + Vite Frontend Application
│       ├── src/
│       │   ├── components/        # Playground, DocumentUpload, AgentGraphVisualizer, AdminDashboard
│       │   ├── services/          # Multi-Provider AI Service & FastAPI API Client
│       │   └── App.jsx
│       ├── package.json
│       └── Dockerfile
├── docs/
│   └── ARCHITECTURE.md            # System Architecture & Diagrams
└── docker-compose.yml             # Docker Compose (frontend, backend, postgres, qdrant)
```

---

## 🔌 API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new user account |
| `POST` | `/api/v1/auth/login` | Login and acquire JWT bearer token |
| `POST` | `/api/v1/documents/upload` | Upload & index PDF/DOCX/TXT into Qdrant |
| `GET` | `/api/v1/documents` | List all indexed enterprise documents |
| `DELETE` | `/api/v1/documents/{id}` | Delete document from vector database |
| `POST` | `/api/v1/chat` | Execute LangGraph 4-Agent RAG workflow |
| `GET` | `/api/v1/history` | Retrieve persistent chat session history |
| `GET` | `/api/v1/metrics` | Fetch evaluation telemetry & observability logs |
| `GET` | `/api/v1/admin/stats` | Fetch admin platform stats & hallucination counts |

---

## 🐳 Docker Deployment Guide

To deploy the entire Enterprise AI Engineering Platform with a single command:

```bash
docker compose up --build
```

### Services Started:
- **Frontend App:** `http://localhost:3000`
- **FastAPI OpenAPI Specs:** `http://localhost:8000/docs`
- **PostgreSQL Database:** `localhost:5432`
- **Qdrant Vector DB:** `http://localhost:6333/dashboard`
