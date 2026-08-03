import os
import sys

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.rag.ingestion import process_and_index_document
from app.agents.workflow import execute_multi_agent_pipeline
from app.rag.vectorstore import search_similar_chunks

def main():
    dataset_path = os.path.join("sample_data", "enterprise_ai_architecture_guide.md")
    filename = "enterprise_ai_architecture_guide.md"

    print("=========================================================")
    print("  Enterprise RAG Pipeline — Real Dataset Ingestion Test  ")
    print("=========================================================")

    # Step 1: Process and Index Real Document
    print(f"\n1. Ingesting Real Dataset: {filename}...")
    ingest_result = process_and_index_document(dataset_path, filename)
    print(f"   [SUCCESS] Indexed into Qdrant Vector Store!")
    print(f"   Raw Text Size: {ingest_result['raw_text_length']} bytes")
    print(f"   Chunks Created & Indexed: {ingest_result['chunk_count']}")

    # Step 2: Query 1 — Target SLA Uptime & Latency
    query1 = "What is the target uptime SLA and maximum retrieval latency for Qdrant?"
    print(f"\n2. Executing Real Query 1: '{query1}'")
    result1 = execute_multi_agent_pipeline(query1, session_id="real_data_session_1")
    
    print("\n   --- Verified Answer ---")
    print(f"   {result1['final_response']}")
    print(f"\n   [METRICS] Latency: {result1['latency_ms']} ms | Confidence: {result1['confidence_score']} | Citations: {result1['citation_count']}")

    # Step 3: Query 2 — Security & Guardrail Policy
    query2 = "What happens if a user submits a prompt injection or DAN mode attempt?"
    print(f"\n\n3. Executing Real Query 2: '{query2}'")
    result2 = execute_multi_agent_pipeline(query2, session_id="real_data_session_2")
    
    print("\n   --- Verified Answer ---")
    print(f"   {result2['final_response']}")
    print(f"\n   [METRICS] Latency: {result2['latency_ms']} ms | Confidence: {result2['confidence_score']} | Citations: {result2['citation_count']}")

    # Step 4: Query 3 — 4-Agent LangGraph Workflow
    query3 = "List the four agents in the LangGraph workflow and their responsibilities."
    print(f"\n\n4. Executing Real Query 3: '{query3}'")
    result3 = execute_multi_agent_pipeline(query3, session_id="real_data_session_3")
    
    print("\n   --- Verified Answer ---")
    print(f"   {result3['final_response']}")
    print(f"\n   [METRICS] Latency: {result3['latency_ms']} ms | Confidence: {result3['confidence_score']} | Citations: {result3['citation_count']}")

    print("\n=========================================================")
    print("  Real Dataset Test Completed Successfully!  ")
    print("=========================================================")

if __name__ == "__main__":
    main()
