import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.rag.ingestion import process_and_index_document
from app.rag.vectorstore import upsert_chunks, _in_memory_docs
from app.agents.workflow import execute_multi_agent_pipeline

DOC_PRICING = """# Acme Cloud — Pricing & Plans (Updated March 2026)

## Plan Overview

| Plan | Price | Seats Included | Storage |
|---|---|---|---|
| Free | $0/mo | 1 | 2 GB |
| Pro | $19/mo or $180/yr | 5 | 100 GB |
| Business | $49/mo or $470/yr | 20 | 1 TB |
| Enterprise | Custom | Unlimited | Custom |

Annual billing gives a discount equivalent to roughly 2 months free compared to monthly billing.

## Refund Note
Refunds for annual plans are processed within 45 days of purchase per March 2026 pricing update.
"""

DOC_REFUND = """# Refund & Support Policy

### 1.1 Monthly Plans
Customers on monthly subscription plans may request a refund within 14 days of the charge date.

### 1.2 Annual Plans
Annual subscriptions have a 30-day refund window from original purchase date.

### 1.3 Support Escalation
Support tickets are answered within 24 hours for Pro plans and 1 hour for Enterprise plans.
"""

DOC_SECURITY = """# Security & Compliance FAQ

### 1. Data Encryption
All customer data is encrypted at rest using AES-256 military-grade encryption standards and TLS 1.3 in transit.

### 2. Access Control
Role-Based Access Control (RBAC) is enforced across all tenant workspaces.
"""

class TestBugsStep4RegressionSuite(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        _in_memory_docs.clear()
        
        # Populate test documents into Qdrant/in-memory vector store
        test_chunks = [
            {
                "text": "[pricing_and_plans.md] Acme Cloud Pricing & Plans. Free $0/mo, Pro $19/mo or $180/yr. Annual billing gives 2 months free. Refunds for annual plans are processed within 45 days of purchase per March 2026 pricing update.",
                "filename": "pricing_and_plans.md",
                "page": 1,
                "chunk_id": 0
            },
            {
                "text": "[refund_and_support_policy.md] Monthly Plans: Customers on monthly subscription plans may request a refund within 14 days of the charge date. Annual Plans: Annual subscriptions have a 30-day refund window from original purchase date.",
                "filename": "refund_and_support_policy.md",
                "page": 1,
                "chunk_id": 1
            },
            {
                "text": "[security_faq.md] Data Encryption: All customer data is encrypted at rest using AES-256 military-grade encryption standards and TLS 1.3 in transit.",
                "filename": "security_faq.md",
                "page": 1,
                "chunk_id": 2
            }
        ]
        upsert_chunks(test_chunks)

    def tearDown(self):
        _in_memory_docs.clear()

    # 1. Step 4 Test 1: Narrow monthly refund query -> "14 days", non-zero confidence, citing refund_and_support_policy.md
    def test_step4_1_monthly_refund_query(self):
        query = "What is the refund window for monthly plans?"
        result = execute_multi_agent_pipeline(query, provider_id="browser")
        
        self.assertIn("14 days", result["final_response"])
        self.assertGreater(result["confidence_score"], 0.0)
        self.assertIn("refund_and_support_policy.md", [c["filename"] for c in result["retrieved_chunks"]])
        print(" [PASS Step 4.1] Monthly refund window query returned '14 days' with non-zero confidence & refund_and_support_policy.md citation")

    # 2. Step 4 Test 2: Annual refund conflict -> surface both 30 days and 45 days
    def test_step4_2_annual_refund_conflict_query(self):
        query = "What is the refund period for annual plans — 30 days or 45 days?"
        result = execute_multi_agent_pipeline(query, provider_id="browser")
        
        self.assertIn("30", result["final_response"])
        self.assertIn("45", result["final_response"])
        print(" [PASS Step 4.2] Annual refund conflict query surfaced both 30 days and 45 days figures")

    # 3. Step 4 Test 3: Encryption standard -> "AES-256" citing security_faq.md
    def test_step4_3_encryption_standard_query(self):
        query = "What encryption standard is used at rest?"
        result = execute_multi_agent_pipeline(query, provider_id="browser")
        
        self.assertIn("AES-256", result["final_response"])
        self.assertIn("security_faq.md", [c["filename"] for c in result["retrieved_chunks"]])
        print(" [PASS Step 4.3] Encryption standard query returned 'AES-256' citing security_faq.md")

    # 4. Step 4 Test 4: Out of scope query -> "Information not found", Confidence: 0
    def test_step4_4_out_of_scope_query(self):
        _in_memory_docs.clear() # Force 0 chunks
        query = "What are the key integration providers available in the enterprise system?"
        with patch("app.agents.workflow.search_similar_chunks", return_value=[]):
            result = execute_multi_agent_pipeline(query, provider_id="browser")
        
        self.assertEqual(result["confidence_score"], 0.0)
        self.assertTrue(result["is_hallucinated"])
        self.assertIn("Information not found", result["final_response"])
        print(" [PASS Step 4.4] Out-of-scope query returned 'Information not found' with Confidence: 0")

    # 5. Step 4 Test 5: Multi-part query -> answers both parts
    def test_step4_5_multipart_query(self):
        query = "What is the refund window for monthly plans? What encryption standard is used at rest?"
        result = execute_multi_agent_pipeline(query, provider_id="browser")
        
        self.assertIn("14 days", result["final_response"])
        self.assertIn("AES-256", result["final_response"])
        print(" [PASS Step 4.5] Multi-part query answered both 14 days refund window and AES-256 encryption")

if __name__ == "__main__":
    unittest.main()
