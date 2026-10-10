import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.core.config import settings
from app.rag import vectorstore


class TestRetrieval(unittest.TestCase):
    def setUp(self):
        vectorstore._in_memory_docs.clear()

    def tearDown(self):
        vectorstore._in_memory_docs.clear()

    def test_embedding_model_outputs_vectors(self):
        class FakeEmbeddingModel:
            def embed(self, texts):
                self.texts = texts
                return [SimpleNamespace(tolist=lambda: [0.1] * 384) for _ in texts]

        fake_model = FakeEmbeddingModel()
        with patch.object(vectorstore, "_embedding_model", return_value=fake_model):
            result = vectorstore.embed_texts(["new user content"])

        self.assertEqual(fake_model.texts, ["new user content"])
        self.assertEqual(len(result[0]), vectorstore.EMBEDDING_DIMENSION)

    def test_hybrid_search_includes_semantically_retrieved_passage(self):
        semantic_doc = {
            "text": "Staff members receive twenty paid leave days each calendar year.",
            "filename": "employee-benefits.txt",
            "page": 2,
            "chunk_id": 3,
        }
        lexical_doc = {
            "text": "Employee PTO requests must be submitted to a manager.",
            "filename": "time-off-policy.txt",
            "page": 1,
            "chunk_id": 0,
        }
        vectorstore._in_memory_docs.append(lexical_doc)

        class FakeQdrant:
            def query_points(self, **kwargs):
                return SimpleNamespace(
                    points=[
                        SimpleNamespace(payload=semantic_doc, score=0.91),
                    ]
                )

        with (
            patch.object(vectorstore, "get_qdrant_client", return_value=FakeQdrant()),
            patch.object(vectorstore, "embed_texts", return_value=[[0.2] * 384]),
        ):
            results = vectorstore.search_similar_chunks("vacation allowance", top_k=2)

        self.assertEqual(results[0]["filename"], "employee-benefits.txt")
        self.assertEqual(len(results), 1)
        self.assertGreater(results[0]["score"], 0)

    def test_bm25_retrieves_arbitrary_new_document_without_seed_data(self):
        vectorstore.upsert_chunks(
            [
                {
                    "text": "The observatory telescope is calibrated every six months.",
                    "filename": "observatory-manual.txt",
                    "page": 1,
                    "chunk_id": 0,
                },
                {
                    "text": "Staff submit vacation requests through the HR portal.",
                    "filename": "employee-guide.txt",
                    "page": 1,
                    "chunk_id": 0,
                },
            ]
        )
        with patch.object(vectorstore, "get_qdrant_client", return_value=None):
            results = vectorstore.search_similar_chunks(
                "observatory telescope calibration", top_k=1
            )

        self.assertEqual(results[0]["filename"], "observatory-manual.txt")

    def test_legacy_collection_migration_reembeds_without_deleting_source(self):
        legacy_record = SimpleNamespace(
            id="legacy-point-1",
            payload={
                "text": "A legacy document chunk",
                "filename": "legacy.txt",
                "page": 1,
                "chunk_id": 0,
            },
        )

        class FakeQdrant:
            def __init__(self):
                self.upserted = []

            def get_collections(self):
                return SimpleNamespace(
                    collections=[
                        SimpleNamespace(name=settings.LEGACY_QDRANT_COLLECTION)
                    ]
                )

            def scroll(self, **kwargs):
                return [legacy_record], None

            def upsert(self, **kwargs):
                self.upserted.extend(kwargs["points"])

        client = FakeQdrant()
        with patch.object(vectorstore, "embed_texts", return_value=[[0.3] * 384]):
            vectorstore._migrate_legacy_collection(client)

        self.assertEqual(len(client.upserted), 1)
        self.assertEqual(client.upserted[0].id, legacy_record.id)
        self.assertEqual(client.upserted[0].vector, [0.3] * 384)
        self.assertEqual(legacy_record.payload["text"], "A legacy document chunk")


if __name__ == "__main__":
    unittest.main()
