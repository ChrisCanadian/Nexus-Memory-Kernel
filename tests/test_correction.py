from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus_memory_kernel import MemoryStore, MemoryCapabilityExecutor, TrustedScope

class CorrectionTests(unittest.TestCase):
    def test_correction_preserves_lineage(self):
        store = MemoryStore()
        ex = MemoryCapabilityExecutor(store)
        scope = TrustedScope("u1", "s1")

        first = ex.execute(
            capability="memory.store",
            arguments={"content": "favorite color is red"},
            scope=scope,
            allow_writes=True,
        )
        old_id = first.data["memory_id"]

        corrected = ex.execute(
            capability="memory.correct",
            arguments={"memory_id": old_id, "replacement": "favorite color is blue"},
            scope=scope,
            allow_writes=True,
        )
        self.assertTrue(corrected.ok)
        self.assertEqual(corrected.data["current"]["supersedes_id"], old_id)

        old = ex.execute(
            capability="memory.inspect",
            arguments={"memory_id": old_id},
            scope=scope,
        )
        self.assertEqual(old.data["status"], "superseded")

        active = ex.execute(
            capability="memory.search",
            arguments={"query": "favorite color"},
            scope=scope,
        )
        self.assertEqual(len(active.data), 1)
        self.assertIn("blue", active.data[0]["content"])
        store.close()

if __name__ == "__main__":
    unittest.main()
