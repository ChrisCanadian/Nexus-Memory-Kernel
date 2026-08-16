from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus_memory_kernel import MemoryStore, MemoryCapabilityExecutor, TrustedScope

class ReverseRanker:
    def __init__(self):
        self.called = False

    def rank(self, query, candidates, limit):
        self.called = True
        return list(reversed(list(candidates)))[:limit]

class SemanticAdapterTests(unittest.TestCase):
    def test_semantic_adapter_only_receives_scoped_candidates(self):
        store = MemoryStore()
        alpha = TrustedScope("alpha", "s1")
        beta = TrustedScope("beta", "s1")
        store.store(alpha, content="shared term alpha one")
        store.store(alpha, content="shared term alpha two")
        store.store(beta, content="shared term beta secret")

        ranker = ReverseRanker()
        executor = MemoryCapabilityExecutor(store, semantic_ranker=ranker)
        result = executor.execute(
            capability="memory.search",
            arguments={"query": "shared term", "semantic": True, "limit": 10},
            scope=alpha,
        )
        self.assertTrue(result.ok)
        self.assertTrue(ranker.called)
        self.assertEqual(len(result.data), 2)
        self.assertTrue(all(item["user_id"] == "alpha" for item in result.data))
        store.close()

if __name__ == "__main__":
    unittest.main()
