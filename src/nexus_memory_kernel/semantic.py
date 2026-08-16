from typing import Protocol, Sequence
from .models import MemoryRecord

class SemanticRanker(Protocol):
    def rank(self, query: str, candidates: Sequence[MemoryRecord], limit: int) -> list[MemoryRecord]:
        ...

class NoSemanticRanker:
    def rank(self, query: str, candidates: Sequence[MemoryRecord], limit: int) -> list[MemoryRecord]:
        return list(candidates)[:limit]
