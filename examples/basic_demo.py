from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus_memory_kernel import MemoryStore, MemoryCapabilityExecutor, TrustedScope

with tempfile.TemporaryDirectory() as tmp:
    store = MemoryStore(Path(tmp) / "demo.sqlite")
    executor = MemoryCapabilityExecutor(store)
    scope = TrustedScope(user_id="demo-user", session_id="session-1")

    created = executor.execute(
        capability="memory.store",
        arguments={"content": "Prefers concise technical explanations."},
        scope=scope,
        allow_writes=True,
    )
    print("STORE:", created.to_dict())

    recalled = executor.execute(
        capability="memory.search",
        arguments={"query": "concise"},
        scope=scope,
    )
    print("SEARCH:", recalled.to_dict())

    store.close()
