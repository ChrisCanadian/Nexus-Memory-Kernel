from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus_memory_kernel import MemoryStore, MemoryCapabilityExecutor, TrustedScope

class AllCapabilitiesIntegrationTests(unittest.TestCase):
    def test_every_registered_capability_executes(self):
        store = MemoryStore()
        executor = MemoryCapabilityExecutor(store)
        scope = TrustedScope("demo-user", "session-a")

        store_result = executor.execute(
            capability="memory.store",
            arguments={"content": "original memory"},
            scope=scope,
            allow_writes=True,
        )
        self.assertTrue(store_result.ok)
        original_id = store_result.data["memory_id"]

        context_result = executor.execute(
            capability="memory.context",
            arguments={"limit": 10},
            scope=scope,
        )
        self.assertTrue(context_result.ok)
        self.assertEqual(len(context_result.data), 1)

        search_result = executor.execute(
            capability="memory.search",
            arguments={"query": "original"},
            scope=scope,
        )
        self.assertTrue(search_result.ok)
        self.assertEqual(len(search_result.data), 1)

        inspect_result = executor.execute(
            capability="memory.inspect",
            arguments={"memory_id": original_id},
            scope=scope,
        )
        self.assertTrue(inspect_result.ok)
        self.assertEqual(inspect_result.data["memory_id"], original_id)

        correct_result = executor.execute(
            capability="memory.correct",
            arguments={
                "memory_id": original_id,
                "replacement": "corrected memory",
            },
            scope=scope,
            allow_writes=True,
        )
        self.assertTrue(correct_result.ok)
        corrected_id = correct_result.data["current"]["memory_id"]
        self.assertEqual(
            correct_result.data["current"]["supersedes_id"],
            original_id,
        )

        supersede_result = executor.execute(
            capability="memory.supersede",
            arguments={"memory_id": corrected_id},
            scope=scope,
            allow_writes=True,
        )
        self.assertTrue(supersede_result.ok)
        self.assertEqual(supersede_result.data["status"], "superseded")

        self.assertEqual(
            set(executor.registry),
            {
                "memory.search",
                "memory.context",
                "memory.inspect",
                "memory.store",
                "memory.correct",
                "memory.supersede",
            },
        )

        store.close()

if __name__ == "__main__":
    unittest.main()
