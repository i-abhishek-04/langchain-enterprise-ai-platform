import time
import re
from typing import Dict, Any, List, TypedDict
import requests
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from app.rag.vectorstore import search_similar_chunks
from app.guardrails.security import validate_input, calculate_dynamic_confidence
from app.core.config import settings

class AgentState(TypedDict):
    query: str
    sanitized_query: str
    sub_queries: List[str]
    session_id: str
    provider_id: str
    model_id: str
    api_key: str
    retrieved_chunks: List[Dict[str, Any]]
    context_text: str
    draft_response: str
    final_response: str
    confidence_score: float
    citation_count: int
    is_hallucinated: bool
    guardrail_flagged: bool
    guardrail_reason: str
    zero_chunk_fallback: bool
    is_fallback_mode: bool
    fallback_reason: str
    agent_logs: List[str]
    latency_ms: float
    total_tokens: int

def decompose_query(query: str) -> List[str]:
    """Decompose multi-part queries (e.g. multiple '?' or 'and') into distinct sub-queries."""
    if "?" in query:
        parts = [p.strip() + "?" for p in query.split("?") if p.strip()]
        return parts if len(parts) > 1 else [query]
    return [query]

def run_document_processing_agent(state: AgentState) -> AgentState:
    """Agent 1: Parses, sanitizes, decomposes multi-part queries, and checks guardrails."""
    is_valid, sanitized, reason = validate_input(state["query"])
    state["sanitized_query"] = sanitized
    
    sub_qs = decompose_query(sanitized)
    state["sub_queries"] = sub_qs
    
    if len(sub_qs) > 1:
        state["agent_logs"].append(f"[Agent 1: Doc Processing] Multi-part query detected. Decomposed into {len(sub_qs)} sub-queries.")
    else:
        state["agent_logs"].append(f"[Agent 1: Doc Processing] Validated query. PII Masked: '{sanitized[:60]}...'")
    
    if not is_valid:
        state["guardrail_flagged"] = True
        state["guardrail_reason"] = reason
        state["agent_logs"].append(f"[Agent 1: Doc Processing] Guardrail Triggered: {reason}")
    return state

def run_retriever_agent(state: AgentState) -> AgentState:
    """Agent 2: Retrieves relevant document chunks from Qdrant vector database."""
    if state["guardrail_flagged"]:
        return state

    all_chunks = []
    seen_texts = set()

    for sub_q in state["sub_queries"]:
        chunks = search_similar_chunks(sub_q, top_k=5)
        for c in chunks:
            if c["text"] not in seen_texts:
                seen_texts.add(c["text"])
                all_chunks.append(c)

    state["retrieved_chunks"] = all_chunks
    
    if not all_chunks:
        state["zero_chunk_fallback"] = True
        state["context_text"] = ""
        state["citation_count"] = 0
        state["agent_logs"].append("[Agent 2: Retriever Agent] No matching chunks found in Qdrant vector store (0 chunks).")
    else:
        state["zero_chunk_fallback"] = False
        context_blocks = [f"Source [{c['filename']}]: {c['text']}" for c in all_chunks]
        state["context_text"] = "\n\n".join(context_blocks)
        state["citation_count"] = len(all_chunks)
        state["agent_logs"].append(f"[Agent 2: Retriever Agent] Retrieved {len(all_chunks)} relevant chunks from Qdrant.")
        
    return state

def run_reasoning_agent(state: AgentState) -> AgentState:
    """Agent 3: Generates answer strictly constrained to retrieved context using free AI providers."""
    if state["guardrail_flagged"]:
        state["draft_response"] = f"Request blocked by Enterprise Guardrails: {state['guardrail_reason']}"
        return state

    if state["zero_chunk_fallback"]:
        state["draft_response"] = "Information not found in indexed enterprise documents."
        state["agent_logs"].append("[Agent 3: Reasoning Agent] Skipped LLM generation due to 0 retrieved chunks.")
        return state

    context = state.get("context_text", "")
    query = state["sanitized_query"]
    provider_id = state.get("provider_id", "groq")
    model_id = state.get("model_id", "llama-3.3-70b-versatile")
    api_key = state.get("api_key", "") or settings.GROQ_API_KEY

    multi_part_note = " Address every distinct sub-question asked." if len(state["sub_queries"]) > 1 else ""

    system_instruction = (
        f"You are an Enterprise AI Reasoning Agent.{multi_part_note} Answer the question directly and accurately using strictly the provided context. "
        "Do not invent facts outside the context. Include source citations if available."
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}"

    response_text = ""
    state["is_fallback_mode"] = False
    state["fallback_reason"] = ""

    if provider_id == "groq" and api_key:
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_instruction),
                    ("human", "Context:\n{context}\n\nQuestion: {query}"),
                ]
            )
            model = ChatOpenAI(
                model=model_id,
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
                temperature=0.2,
                timeout=12.0,
            )
            chain = prompt | model | StrOutputParser()
            response_text = chain.invoke({"context": context, "query": query})
            if not response_text.strip():
                state["is_fallback_mode"] = True
                state["fallback_reason"] = "LangChain returned an empty response."
        except Exception as e:
            state["is_fallback_mode"] = True
            state["fallback_reason"] = f"LangChain Groq model call failed: {str(e)}"

    # Retain the direct API call as a compatibility fallback if LangChain fails.
    if provider_id == "groq" and not response_text:
        if not api_key:
            state["is_fallback_mode"] = True
            state["fallback_reason"] = "Groq API Key is missing. Add free key in Settings."
        else:
            try:
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model_id,
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2
                    },
                    timeout=12.0
                )
                if res.ok:
                    response_text = res.json()["choices"][0]["message"]["content"]
                else:
                    state["is_fallback_mode"] = True
                    state["fallback_reason"] = f"Groq API Error ({res.status_code}). Using local fallback."
            except Exception as e:
                state["is_fallback_mode"] = True
                state["fallback_reason"] = f"Groq Connection Error: {str(e)}"

    if provider_id != "groq":
        state["is_fallback_mode"] = True
        state["fallback_reason"] = (
            f"The backend supports Groq through LangChain; provider '{provider_id}' "
            "uses the local fallback."
        )

    # Return retrieved passages rather than fabricating a model answer.
    if not response_text:
        state["is_fallback_mode"] = True
        if not state["fallback_reason"]:
            state["fallback_reason"] = (
                f"No live model response was available for provider '{provider_id}'. "
                "Returning retrieved passages without synthesis."
            )
        excerpts = [
            f"[{chunk['filename']}, page {chunk.get('page', 1)}]\n{chunk['text']}"
            for chunk in state["retrieved_chunks"]
        ]
        response_text = (
            "No live model response is available. Relevant retrieved passages:\n\n"
            + "\n\n".join(excerpts)
        )

    state["draft_response"] = response_text
    if state["is_fallback_mode"]:
        state["agent_logs"].append(
            f"[Agent 3: Reasoning Agent] Used fallback. {state['fallback_reason']}"
        )
    else:
        state["agent_logs"].append(
            f"[Agent 3: Reasoning Agent] Generated response with LangChain ChatOpenAI "
            f"using {provider_id} ({model_id})."
        )
    return state

def run_verification_agent(state: AgentState) -> AgentState:
    """Agent 4: Checks for hallucination, computes dynamic confidence score, and enforces safety gating."""
    if state["guardrail_flagged"]:
        state["final_response"] = state["draft_response"]
        state["confidence_score"] = 0.0
        state["is_hallucinated"] = True
        return state

    if state["zero_chunk_fallback"]:
        state["final_response"] = "Information not found in indexed enterprise documents."
        state["confidence_score"] = 0.0
        state["is_hallucinated"] = True
        state["agent_logs"].append("[Agent 4: Verification Agent] Zero chunks retrieved. Hallucination check marked FAILED/SKIPPED (Confidence: 0.0).")
        return state

    is_faithful, score = calculate_dynamic_confidence(
        retrieved_chunks=state["retrieved_chunks"],
        response_text=state["draft_response"],
        context_text=state.get("context_text", ""),
        zero_chunks=state["zero_chunk_fallback"]
    )
    
    state["confidence_score"] = score
    state["is_hallucinated"] = not is_faithful

    if score < 0.30 and state.get("context_text"):
        state["final_response"] = "Information not found in indexed enterprise documents."
        state["agent_logs"].append(f"[Agent 4: Verification Agent] Low confidence score ({score}). Hallucination check FAILED.")
    else:
        state["final_response"] = state["draft_response"]
        state["agent_logs"].append(f"[Agent 4: Verification Agent] Verified response. Dynamic Confidence Score: {score} | Hallucination Check: PASSED.")

    return state


def _build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("document_processing", run_document_processing_agent)
    graph.add_node("retriever", run_retriever_agent)
    graph.add_node("reasoning", run_reasoning_agent)
    graph.add_node("verification", run_verification_agent)
    graph.add_edge(START, "document_processing")
    graph.add_edge("document_processing", "retriever")
    graph.add_edge("retriever", "reasoning")
    graph.add_edge("reasoning", "verification")
    graph.add_edge("verification", END)
    return graph.compile()


agent_graph = _build_agent_graph()


def execute_multi_agent_pipeline(
    query: str,
    session_id: str = "default_session",
    provider_id: str = "groq",
    model_id: str = "llama-3.3-70b-versatile",
    api_key: str = ""
) -> Dict[str, Any]:
    """Execute the compiled four-node LangGraph workflow."""
    start_time = time.time()
    
    state: AgentState = {
        "query": query,
        "sanitized_query": query,
        "sub_queries": [query],
        "session_id": session_id,
        "provider_id": provider_id,
        "model_id": model_id,
        "api_key": api_key,
        "retrieved_chunks": [],
        "context_text": "",
        "draft_response": "",
        "final_response": "",
        "confidence_score": 0.0,
        "citation_count": 0,
        "is_hallucinated": False,
        "guardrail_flagged": False,
        "guardrail_reason": "",
        "zero_chunk_fallback": False,
        "is_fallback_mode": False,
        "fallback_reason": "",
        "agent_logs": [],
        "latency_ms": 0.0,
        "total_tokens": len(query.split()) + 120
    }

    result = agent_graph.invoke(state)
    result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
    return result
