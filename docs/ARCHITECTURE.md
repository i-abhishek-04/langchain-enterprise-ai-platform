# Document Q&A Platform Architecture

This document describes the current implementation. It is a prototype; the diagrams do not imply production SLAs or deployment guarantees.

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
        Graph["Compiled LangGraph StateGraph"]
        Ingest["Document Processing & Chunking"]
    end

    subgraph Data ["Data & Vector Layer"]
        Qdrant[("Qdrant Vector Database (Port 6333)")]
        Postgres[("PostgreSQL Database (Port 5432)")]
    end

    subgraph AI ["Backend Model Integration"]
        LCEL["LangChain LCEL"]
        Groq["Groq OpenAI-compatible API"]
    end

    ReactUI <-->|REST API / JSON| Router
    Router --> Auth
    Router --> Guard
    Guard --> Graph
    Ingest --> Qdrant
    Graph -->|Similarity Search| Qdrant
    Graph --> LCEL --> Groq
    Router -->|Persist Logs, History & Metrics| Postgres
```

---

The backend's active LangChain model integration is Groq. The React playground separately makes direct calls to Groq, OpenRouter, or local Ollama; selecting its local simulator does not call a model.

Qdrant stores 384-dimensional FastEmbed `sentence-transformers/all-MiniLM-L6-v2` embeddings. Retrieval fuses semantic results with BM25-style keyword scores. The current implementation loads document text into backend memory for keyword ranking, which limits corpus size. The embedding model downloads on first use and is cached in a persistent Docker volume.

On startup, the backend creates `enterprise_documents_v2` and migrates payloads from the legacy `enterprise_documents` collection by re-embedding the stored text. It leaves the legacy collection intact, so migration can be retried and old data remains available for recovery.

Changing the embedding model requires a new Qdrant collection and re-indexing; vectors from different models must not be mixed.

Without a successful Groq call, the backend returns retrieved passages as excerpts rather than synthesizing topic-specific canned answers.

## LangGraph workflow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Agent1 as DocProc Agent
    participant Agent2 as Retriever Agent
    participant Agent3 as Reasoning Agent
    participant Agent4 as Verification Agent
    participant Qdrant as Qdrant Vector DB
    participant LCEL as LangChain LCEL
    participant LLM as Groq Chat API

    User->>Agent1: Submit Query / Context
    Agent1->>Agent1: Validate & Mask PII & Detect Prompt Injections
    Agent1->>Agent2: Forward Sanitized Query
    Agent2->>Qdrant: Vector Similarity Search
    Qdrant-->>Agent2: Return Top-K Chunks
    Agent2->>Agent3: Context + Query Payload
    Agent3->>LCEL: Prompt | ChatOpenAI | StrOutputParser
    LCEL->>LLM: Constrained Generation Request
    LLM-->>Agent3: Draft Response Text
    Agent3->>Agent4: Draft Response + Context
    Agent4->>Agent4: Check Faithfulness & Hallucination Score
    alt Confidence Score >= 0.30
        Agent4-->>User: Return Verified Answer + Citations
    else Confidence Score < 0.30
        Agent4-->>User: Return "Information not found in indexed enterprise documents."
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
│   │   │   ├── agents/            # LangGraph workflow and LangChain model call
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
