# Public Boundary

This repository is a **bounded reference implementation**, not a sanitized copy of the private Nexus runtime.

## Included

- generic scoped memory records;
- SQLite reference persistence;
- session and temporal recall;
- keyword filtering;
- correction and supersession;
- provenance metadata;
- a memory-only capability registry;
- a memory-only execution gateway;
- optional semantic-ranking interface;
- synthetic tests and examples.

## Excluded

- production schemas or query implementation;
- private context-selection and composition logic;
- private identity or behavioral-state composition;
- global capability/tool orchestration;
- provider/model infrastructure;
- production configuration, endpoints, or deployment details;
- credentials, real user data, conversations, memories, traces, or logs.

## Rule

> Publish the responsibility boundary, not the production assembly line.
