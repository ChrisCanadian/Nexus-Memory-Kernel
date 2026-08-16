from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus_memory_kernel import MemoryStore, MemoryCapabilityExecutor, TrustedScope

class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.executor = MemoryCapabilityExecutor(self.store)
        self.alpha = TrustedScope("alpha", "s1")
        self.beta = TrustedScope("beta", "s1")
        result = self.executor.execute(
            capability="memory.store",
            arguments={"content": "alpha private memory"},
            scope=self.alpha,
            allow_writes=True,
        )
        self.alpha_id = result.data["memory_id"]

    def tearDown(self):
        self.store.close()

    def test_cross_user_search_is_isolated(self):
        result = self.executor.execute(
            capability="memory.search",
            arguments={"query": "private"},
            scope=self.beta,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.data, [])

    def test_cross_user_inspect_fails(self):
        result = self.executor.execute(
            capability="memory.inspect",
            arguments={"memory_id": self.alpha_id},
            scope=self.beta,
        )
        self.assertFalse(result.ok)

    def test_cross_user_correct_fails(self):
        result = self.executor.execute(
            capability="memory.correct",
            arguments={
                "memory_id": self.alpha_id,
                "replacement": "hijacked",
            },
            scope=self.beta,
            allow_writes=True,
        )
        self.assertFalse(result.ok)

    def test_cross_user_supersede_fails(self):
        result = self.executor.execute(
            capability="memory.supersede",
            arguments={"memory_id": self.alpha_id},
            scope=self.beta,
            allow_writes=True,
        )
        self.assertFalse(result.ok)

if __name__ == "__main__":
    unittest.main()
