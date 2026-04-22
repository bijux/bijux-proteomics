# Architecture

`bijux-proteomics-runtime` is the canonical execution layer in the proteomics
package family.

## Responsibility

The runtime layer coordinates how workflows run; it does not define what the
scientific meaning is.

Runtime-owned capabilities:

- CLI and operator entrypoint routing
- HTTP API wiring for runtime operations
- provider binding and provider execution adapters
- runtime state machine and execution control
- workspace and run artifact lifecycle
- replay and determinism enforcement
- orchestration across foundation/core/knowledge/intelligence/lab

## Execution model

The runtime layer composes lower-layer package capabilities and exposes
execution surfaces to users and automation.

```mermaid
flowchart TD
    CLI[CLI] --> RT[Runtime Orchestrator]
    API[HTTP API] --> RT
    RT --> FOUNDATION[Foundation]
    RT --> CORE[Core]
    RT --> KNOWLEDGE[Knowledge]
    RT --> INTELLIGENCE[Intelligence]
    RT --> LAB[Lab]
    RT --> ARTIFACTS[Workspace and Artifacts]
    RT --> REPLAY[Replay and Determinism]
```

## Design constraints

- Runtime composes lower layers but never redefines their domain truth.
- Runtime adapts lower-layer models for execution and transport boundaries.
- Runtime keeps operator interfaces stable while internal orchestration evolves.

## Adapter topology

Runtime adapter modules are the only place where lower-layer domain objects are
translated into runtime interface payloads.

- `runtime/adapters/candidates.py`: candidate model mapping and selection wiring
- `runtime/adapters/quality.py`: quality and reliability mapping
- `runtime/adapters/memory.py`: memory record mapping
- `runtime/adapters/design_loop.py`: design-loop orchestration contracts
- `runtime/adapters/lab.py`: lab planning and evidence-promotion entrypoints

This keeps lower packages runtime-agnostic and prevents upward leakage of
runtime-specific schemas.
