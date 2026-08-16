from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus_memory_kernel import MemoryStore, MemoryCapabilityExecutor, TrustedScope

class PersistenceTests(unittest.TestCase):
    def test_reopen_preserves_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "memory.sqlite"
            scope = TrustedScope("u1", "s1")

            store = MemoryStore(db)
            store.store(scope, content="survives reopen")
            store.close()

            reopened = MemoryStore(db)
            found = reopened.search(scope, query="survives")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].content, "survives reopen")
            reopened.close()

if __name__ == "__main__":
    unittest.main()
