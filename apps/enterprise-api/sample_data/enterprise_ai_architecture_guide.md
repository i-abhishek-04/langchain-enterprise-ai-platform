# Enterprise AI Engineering Platform Architecture & Operational Guidelines (v2.4)

## 1. System Overview & Core Capabilities
The Enterprise AI Engineering Platform is designed for high-throughput, low-latency agentic workflows and retrieval-augmented generation (RAG). The platform leverages LangChain LCEL for component composition, LangGraph for stateful multi-agent orchestration, Qdrant for dense vector retrieval, and PostgreSQL for telemetry and observability.

## 2. High Availability & Service Level Agreements (SLAs)
- **Target Uptime:** 99.95% availability across production deployments.
- **Maximum Retrieval Latency:** Sub-50 milliseconds for Qdrant vector similarity search queries.
- **Maximum End-to-End Latency:** Less than 1,500 milliseconds for 4-agent LangGraph workflow execution.
- **Token Throughput:** Supported up to 120 tokens per second using free-tier acceleration engines (Groq Cloud Llama 3.3 70B & Google Gemini 2.0 Flash).

## 3. Security, Compliance & Guardrails Policy
All incoming queries and documents must pass through automated Python security middleware prior to processing:
1. **PII Masking:** Personally Identifiable Information (PII) including email addresses, telephone numbers, Social Security Numbers (SSN), and credit card numbers are automatically masked with placeholders (`[MASKED_EMAIL]`, `[MASKED_PHONE]`, `[MASKED_SSN]`).
2. **Prompt Injection & Jailbreak Defense:** System prompt overrides, role-reversal attacks, and DAN-mode bypasses trigger an immediate HTTP 400 rejection and flag an event in PostgreSQL observability logs.
3. **Context Boundary Enforcement:** The Verification Agent evaluates answer faithfulness against retrieved Qdrant context. If the confidence score drops below 0.65, the system responds with: *"I don't have enough information."*

## 4. Multi-Agent Orchestration Workflow (LangGraph)
The platform executes queries through a stateful 4-agent graph:
- **Agent 1 (Document Processing):** Performs content cleaning, chunking (500 tokens, 50 overlap), and PII sanitization.
- **Agent 2 (Retriever Agent):** Generates 384-dimensional dense embeddings and queries Qdrant for top-k relevant document chunks.
- **Agent 3 (Reasoning Agent):** Synthesizes grounded answers strictly constrained to retrieved context using free-tier LLM backends.
- **Agent 4 (Verification Agent):** Verifies citations, calculates hallucination scores, and enforces final response safety.

## 5. Storage Architecture
- **Qdrant Vector Database:** Stores dense vector embeddings and metadata payloads (`filename`, `page`, `chunk_id`).
- **PostgreSQL Database:** Persists `users`, `documents`, `chat_history`, and `evaluation_logs`.
