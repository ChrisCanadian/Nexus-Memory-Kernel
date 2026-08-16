from __future__ import annotations

from typing import Any

from .models import CapabilityResult, TrustedScope
from .receipts import make_receipt
from .registry import CapabilitySpec, build_default_registry
from .semantic import NoSemanticRanker, SemanticRanker
from .store import MemoryStore

class MemoryCapabilityExecutor:
    """
    Bounded memory-only execution gateway.

    This is intentionally not a copy of the private Nexus ToolExecutor.
    Trusted scope and write authority are supplied by the host and cannot
    be selected or escalated through capability arguments.
    """

    def __init__(
        self,
        store: MemoryStore,
        *,
        registry: dict[str, CapabilitySpec] | None = None,
        semantic_ranker: SemanticRanker | None = None,
    ) -> None:
        self.store = store
        self.registry = registry or build_default_registry()
        self.semantic_ranker = semantic_ranker or NoSemanticRanker()

    def execute(
        self,
        *,
        capability: str,
        arguments: dict[str, Any],
        scope: TrustedScope,
        allow_writes: bool = False,
    ) -> CapabilityResult:
        spec = self.registry.get(capability)
        if spec is None:
            return CapabilityResult(False, capability, error="unknown memory capability")

        if spec.authority == "write" and not allow_writes:
            return CapabilityResult(False, capability, error="write authority not granted")

        supplied = frozenset(arguments)
        missing = spec.required_args - supplied
        unexpected = supplied - spec.allowed_args

        if missing:
            return CapabilityResult(
                False,
                capability,
                error="missing required arguments: " + ", ".join(sorted(missing)),
            )
        if unexpected:
            return CapabilityResult(
                False,
                capability,
                error="unexpected arguments: " + ", ".join(sorted(unexpected)),
            )

        try:
            handler = getattr(self, f"_handle_{spec.handler_name}")
            return handler(scope=scope, arguments=arguments)
        except (KeyError, ValueError, TypeError) as exc:
            return CapabilityResult(False, capability, error=str(exc))

    def _handle_search(self, *, scope: TrustedScope, arguments: dict[str, Any]) -> CapabilityResult:
        requested_limit = max(1, min(int(arguments.get("limit", 10)), 100))
        semantic = bool(arguments.get("semantic", False))
        candidate_limit = min(requested_limit * 5, 100) if semantic else requested_limit

        records = self.store.search(
            scope,
            query=str(arguments.get("query", "")),
            start_at=arguments.get("start_at"),
            end_at=arguments.get("end_at"),
            limit=candidate_limit,
            include_superseded=bool(arguments.get("include_superseded", False)),
        )

        if semantic and arguments.get("query"):
            records = self.semantic_ranker.rank(
                str(arguments["query"]),
                records,
                requested_limit,
            )
        else:
            records = records[:requested_limit]

        return CapabilityResult(
            True,
            "memory.search",
            data=[record.to_dict() for record in records],
        )

    def _handle_context(self, *, scope: TrustedScope, arguments: dict[str, Any]) -> CapabilityResult:
        records = self.store.context(
            scope,
            limit=max(1, min(int(arguments.get("limit", 20)), 100)),
        )
        return CapabilityResult(
            True,
            "memory.context",
            data=[record.to_dict() for record in records],
        )

    def _handle_inspect(self, *, scope: TrustedScope, arguments: dict[str, Any]) -> CapabilityResult:
        record = self.store.get(scope, str(arguments["memory_id"]))
        if record is None:
            raise KeyError("memory not found in trusted scope")
        return CapabilityResult(True, "memory.inspect", data=record.to_dict())

    def _handle_store(self, *, scope: TrustedScope, arguments: dict[str, Any]) -> CapabilityResult:
        content = str(arguments["content"]).strip()
        if not content:
            raise ValueError("content must not be empty")

        record = self.store.store(
            scope,
            content=content,
            source="memory-capability",
        )
        receipt = make_receipt(
            action="memory.store",
            user_id=scope.user_id,
            target_id=record.memory_id,
            payload={"content": content, "session_id": scope.session_id},
        )
        return CapabilityResult(
            True,
            "memory.store",
            data=record.to_dict(),
            receipt=receipt,
        )

    def _handle_correct(self, *, scope: TrustedScope, arguments: dict[str, Any]) -> CapabilityResult:
        replacement = str(arguments["replacement"]).strip()
        if not replacement:
            raise ValueError("replacement must not be empty")

        previous, current = self.store.correct(
            scope,
            memory_id=str(arguments["memory_id"]),
            replacement=replacement,
            source="memory-correction",
        )
        receipt = make_receipt(
            action="memory.correct",
            user_id=scope.user_id,
            target_id=current.memory_id,
            payload={
                "supersedes_id": previous.memory_id,
                "replacement": replacement,
            },
        )
        return CapabilityResult(
            True,
            "memory.correct",
            data={
                "previous": previous.to_dict(),
                "current": current.to_dict(),
            },
            receipt=receipt,
        )

    def _handle_supersede(self, *, scope: TrustedScope, arguments: dict[str, Any]) -> CapabilityResult:
        memory_id = str(arguments["memory_id"])
        record = self.store.supersede(scope, memory_id=memory_id)
        receipt = make_receipt(
            action="memory.supersede",
            user_id=scope.user_id,
            target_id=memory_id,
            payload={"status": "superseded"},
        )
        return CapabilityResult(
            True,
            "memory.supersede",
            data=record.to_dict(),
            receipt=receipt,
        )
