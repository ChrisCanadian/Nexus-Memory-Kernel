from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus_memory_kernel import MemoryStore, MemoryCapabilityExecutor, TrustedScope

class TemporalTests(unittest.TestCase):
    def test_time_bounds_are_applied(self):
        store = MemoryStore()
        scope = TrustedScope("u1", "s1")

        first = store.store(scope, content="first")
        second = store.store(scope, content="second")

        found = store.search(scope, start_at=second.created_at, limit=10)
        self.assertGreaterEqual(len(found), 1)
        self.assertTrue(all(item.created_at >= second.created_at for item in found))
        store.close()

if __name__ == "__main__":
    unittest.main()
