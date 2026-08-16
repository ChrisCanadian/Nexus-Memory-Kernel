from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus_memory_kernel import MemoryStore, MemoryCapabilityExecutor, TrustedScope

class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.executor = MemoryCapabilityExecutor(self.store)
        self.scope = TrustedScope("u1", "s1")

    def tearDown(self):
        self.store.close()

    def test_unknown_capability_is_rejected(self):
        result = self.executor.execute(
            capability="memory.nope",
            arguments={},
            scope=self.scope,
        )
        self.assertFalse(result.ok)

    def test_write_requires_host_authority(self):
        result = self.executor.execute(
            capability="memory.store",
            arguments={"content": "hello"},
            scope=self.scope,
            allow_writes=False,
        )
        self.assertFalse(result.ok)
        self.assertIn("write authority", result.error)

    def test_scope_injection_is_rejected_as_unexpected_argument(self):
        result = self.executor.execute(
            capability="memory.search",
            arguments={"query": "x", "user_id": "attacker"},
            scope=self.scope,
        )
        self.assertFalse(result.ok)
        self.assertIn("unexpected arguments", result.error)

    def test_provenance_forgery_is_rejected(self):
        result = self.executor.execute(
            capability="memory.store",
            arguments={"content": "hello", "source": "pretend-system"},
            scope=self.scope,
            allow_writes=True,
        )
        self.assertFalse(result.ok)
        self.assertIn("unexpected arguments", result.error)

    def test_missing_required_arguments_are_rejected(self):
        result = self.executor.execute(
            capability="memory.correct",
            arguments={"memory_id": "x"},
            scope=self.scope,
            allow_writes=True,
        )
        self.assertFalse(result.ok)
        self.assertIn("replacement", result.error)

    def test_store_emits_receipt(self):
        result = self.executor.execute(
            capability="memory.store",
            arguments={"content": "remember this"},
            scope=self.scope,
            allow_writes=True,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.receipt["action"], "memory.store")
        self.assertEqual(result.data["source"], "memory-capability")

if __name__ == "__main__":
    unittest.main()
