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
    print("  Document Q&A — Sample Data Ingestion Test  ")
    print("=========================================================")

    # Step 1: Process and Index Real Document
    print(f"\n1. Ingesting Real Dataset: {filename}...")
    ingest_result = process_and_index_document(dataset_path, filename)
    print(f"   Processed and indexed {filename}.")
    print(f"   Raw Text Size: {ingest_result['raw_text_length']} bytes")
    print(f"   Chunks Created & Indexed: {ingest_result['chunk_count']}")

    # Step 2: Query 1 — Frameworks used by the backend
    query1 = "What does the backend use to orchestrate its workflow and call Groq?"
    print(f"\n2. Executing Sample Query 1: '{query1}'")
    result1 = execute_multi_agent_pipeline(query1, session_id="real_data_session_1")
    
    print("\n   --- Pipeline Response ---")
    print(f"   {result1['final_response']}")
    print(f"\n   [METRICS] Latency: {result1['latency_ms']} ms | Confidence: {result1['confidence_score']} | Citations: {result1['citation_count']}")

    # Step 3: Query 2 — Fallback behavior
    query2 = "What does the backend do when a live model response is unavailable?"
    print(f"\n\n3. Executing Sample Query 2: '{query2}'")
    result2 = execute_multi_agent_pipeline(query2, session_id="real_data_session_2")
    
    print("\n   --- Pipeline Response ---")
    print(f"   {result2['final_response']}")
    print(f"\n   [METRICS] Latency: {result2['latency_ms']} ms | Confidence: {result2['confidence_score']} | Citations: {result2['citation_count']}")

    # Step 4: Query 3 — LangGraph workflow
    query3 = "List the four nodes in the LangGraph workflow."
    print(f"\n\n4. Executing Sample Query 3: '{query3}'")
    result3 = execute_multi_agent_pipeline(query3, session_id="real_data_session_3")
    
    print("\n   --- Pipeline Response ---")
    print(f"   {result3['final_response']}")
    print(f"\n   [METRICS] Latency: {result3['latency_ms']} ms | Confidence: {result3['confidence_score']} | Citations: {result3['citation_count']}")

    print("\n=========================================================")
    print("  Sample Data Test Completed  ")
    print("=========================================================")

if __name__ == "__main__":
    main()
