# Document Q&A Platform: Current Implementation

This sample document describes the current repository implementation, not a production deployment or service-level commitment.

## Backend workflow

The FastAPI backend runs a compiled LangGraph `StateGraph` with four sequential nodes:

1. Document processing validates and sanitizes the query.
2. Retrieval searches Qdrant, with an in-memory lexical fallback.
3. Reasoning runs a LangChain LCEL chain using `ChatPromptTemplate`, `ChatOpenAI`, and `StrOutputParser` for Groq. When a live model call is unavailable, the backend returns retrieved passages without synthesizing an answer.
4. Verification calculates a heuristic confidence score from retrieved context and response text. It is not an independent model-based fact checker.

## Retrieval limitations

Qdrant stores 384-dimensional FastEmbed `sentence-transformers/all-MiniLM-L6-v2` vectors. Retrieval combines semantic similarity with BM25-style keyword ranking. The current implementation loads document text into backend memory for keyword ranking. The embedding model downloads on first use and is cached persistently in Docker Compose.

On startup, chunks from the legacy `enterprise_documents` Qdrant collection are re-embedded into `enterprise_documents_v2`. The old collection is retained.

## Other components

- The API accepts PDF, DOCX, TXT, and Markdown uploads.
- The React playground calls Groq, OpenRouter, and local Ollama directly. Other configured selections use a local simulation.
- SQLAlchemy persists application records. Docker Compose configures PostgreSQL; local configuration defaults to SQLite.
- Reported token counts, costs, and confidence values are estimates or heuristics, not provider billing data or independent factuality measurements.
