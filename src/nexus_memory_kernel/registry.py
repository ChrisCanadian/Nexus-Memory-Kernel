from dataclasses import dataclass

@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    authority: str
    handler_name: str
    required_args: frozenset[str]
    optional_args: frozenset[str]
    description: str

    @property
    def allowed_args(self) -> frozenset[str]:
        return self.required_args | self.optional_args

def build_default_registry() -> dict[str, CapabilitySpec]:
    specs = [
        CapabilitySpec(
            "memory.search", "read", "search",
            frozenset(),
            frozenset({"query", "start_at", "end_at", "limit", "include_superseded", "semantic"}),
            "Search memory already constrained to trusted scope.",
        ),
        CapabilitySpec(
            "memory.context", "read", "context",
            frozenset(),
            frozenset({"limit"}),
            "Return bounded context for the trusted session.",
        ),
        CapabilitySpec(
            "memory.inspect", "read", "inspect",
            frozenset({"memory_id"}),
            frozenset(),
            "Inspect one memory inside trusted scope.",
        ),
        CapabilitySpec(
            "memory.store", "write", "store",
            frozenset({"content"}),
            frozenset(),
            "Persist a new memory inside trusted scope.",
        ),
        CapabilitySpec(
            "memory.correct", "write", "correct",
            frozenset({"memory_id", "replacement"}),
            frozenset(),
            "Create a corrected successor while preserving lineage.",
        ),
        CapabilitySpec(
            "memory.supersede", "write", "supersede",
            frozenset({"memory_id"}),
            frozenset(),
            "Mark a memory as superseded without deleting its history.",
        ),
    ]
    return {spec.name: spec for spec in specs}
