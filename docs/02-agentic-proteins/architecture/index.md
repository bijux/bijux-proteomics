---
title: Architecture
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Architecture

`agentic-proteins` architecture is the map of a shrinking compatibility
bridge. The point of this section is not to admire the old structure. The point
is to show exactly how legacy entrypoints are kept alive while canonical
ownership already lives elsewhere.

```mermaid
flowchart LR
    legacy["legacy callers<br/>imports, CLI, API"]
    interfaces["compatibility entrypoints<br/>interfaces, api"]
    bridge["legacy bridge logic<br/>core, execution, providers"]
    runtime["runtime forwarding seam<br/>runtime, workspace, control"]
    canonical["canonical packages<br/>runtime and lower layers"]
    artifacts["reports and state<br/>memory, state, report"]

    legacy --> interfaces
    interfaces --> bridge
    bridge --> runtime
    bridge --> artifacts
    runtime --> canonical
```

## What This Diagram Is Saying

- readers should be able to separate preserved entrypoints from canonical
  ownership in a few seconds
- the bridge still has real structure, but that structure exists to forward,
  constrain, and expose migration proof rather than reclaim authority
- if a module starts to look like the only place behavior can live, the package
  is drifting back into permanence

## Start With

- open [Execution Model](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/execution-model/)
  when you need to follow a legacy import, CLI call, or API request until it
  reaches canonical runtime ownership
- open [Integration Seams](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/integration-seams/)
  when a change risks moving real authority back into the compatibility layer
- open [Module Map](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/module-map/)
  when you already know the question and need the owning files quickly

## Reading Lenses

- [Module Map](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/module-map/)
  for the named bridge families: interfaces, runtime seams, providers, memory,
  state, and reporting
- [Dependency Direction](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/dependency-direction/)
  for the rule that dependencies should keep pointing toward canonical packages,
  not away from them
- [State and Persistence](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/state-and-persistence/)
  and [Error Model](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/error-model/)
  for the surfaces most likely to trap accidental permanence
- [Architecture Risks](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/architecture-risks/)
  for the failure modes that matter more than stylistic purity

## Fast Proof Points

- `src/agentic_proteins/interfaces/`, `api/`, and `runtime/` for the
  public-to-runtime handoff
- `src/agentic_proteins/core/`, `execution/`, and `validation/` for bridge-side
  control logic that still has to exist
- `src/agentic_proteins/providers/`, `memory/`, `state/`, and `report/` for
  the adapter and artifact surfaces most exposed to legacy coupling

## Boundary Test

If a reviewer cannot point to the forwarding seam and the canonical owner in the
same explanation, the architecture is still hiding the real system.
