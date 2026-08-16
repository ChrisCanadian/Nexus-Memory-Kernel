from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class TrustedScope:
    """Scope supplied by the trusted host, never by model arguments."""
    user_id: str
    session_id: str | None = None

@dataclass
class MemoryRecord:
    memory_id: str
    user_id: str
    session_id: str | None
    content: str
    created_at: str
    updated_at: str
    status: str
    source: str
    supersedes_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class CapabilityResult:
    ok: bool
    capability: str
    data: Any = None
    error: str | None = None
    receipt: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
