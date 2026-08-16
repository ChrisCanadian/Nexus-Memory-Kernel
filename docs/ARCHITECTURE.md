# Architecture

## Why an execution gateway belongs in a memory kernel

Storage and retrieval are only part of the responsibility.

A host also needs a boundary that decides whether a proposed memory operation is valid for the already-authenticated scope and whether it is read-only or mutating.

The public `MemoryCapabilityExecutor` demonstrates:

- proposal versus execution authority;
- trusted host scope versus caller-provided arguments;
- read versus write capability classes;
- strict argument validation;
- bounded dispatch;
- normalized results;
- mutation receipts.

It is deliberately **memory-only** and deliberately not a general-purpose runtime executor.

## Flow

```text
model or application
      |
      | proposes memory capability
      v
Memory Capability Registry
      |
      v
Memory Capability Executor
      |
      +-- validates capability and arguments
      +-- receives scope only from trusted host
      +-- enforces read/write authority
      +-- dispatches bounded memory operation
      |
      v
Scoped Memory Store
      |
      +-- persistent records
      +-- temporal filtering
      +-- session context
      +-- correction lineage
      +-- supersession
      |
      +----> optional SemanticRanker
      |
      v
result + optional mutation receipt
```

## Semantic ranking

Semantic ranking is optional.

The durable store remains authoritative. A semantic adapter receives candidates **after scope has already been enforced** and may only rank those candidates.

## Correction model

Corrections preserve the earlier record:

```text
old memory (active)
      |
      | correction
      v
old memory (superseded) ----> corrected memory (active)
                               supersedes_id = old memory
```

No delete is required to make a correction authoritative.
