---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Module map

`agentic-proteins` is a compatibility distribution for historical runtime
imports and the `agentic-proteins` command. Its source tree preserves the old
namespace while canonical implementations live in
`bijux_proteomics_runtime`. In the current package, 111 of 117 Python modules
import from runtime; that ratio is the architectural fact readers need before
mistaking this tree for a second execution engine.

```mermaid
flowchart LR
    legacy["Historical agentic_proteins import"]
    facade["Compatibility module"]
    runtime["bijux_proteomics_runtime owner"]
    core["bijux_proteomics scientific core"]

    legacy --> facade --> runtime --> core
```

## Compatibility families

| Historical namespace | Canonical runtime owner | Preserved responsibility |
| --- | --- | --- |
| package root | runtime package root | `AppConfig`, `RunManager`, `cli`, `create_app` |
| `interfaces` | `runtime.api` | CLI, HTTP application, middleware, routes, and schemas |
| `agents` | `runtime.execution.agents` | planning, coordination, analysis, verification, and reporting imports |
| `execution` | `runtime.execution` and `runtime.runs` | compiler, engine, evaluation, validation, state, artifacts, logging, and telemetry |
| `orchestration` | `runtime.execution`, `runtime.runs`, and runtime governance | historical orchestration spelling plus bridge contracts |
| `providers` | `runtime.providers` | provider contracts, selection, capabilities, local and remote adapters |
| `state` | `runtime.state`, `runtime.runs`, and runtime support | snapshots, lifecycle, context, output, request, and workspace imports |
| `tools` | `runtime.execution.tools` | tool contracts, catalog, schemas, and heuristic tool |

## Why both `execution` and `orchestration` exist

They preserve two historical import families. Both forward to the same runtime
owners and must not evolve as parallel implementations. New execution behavior
belongs in runtime. A compatibility change here is justified only when it keeps
an existing import working, records a bridge contract, or makes retirement
safer.

## Small bridge-owned surface

The package root resolves its four public names lazily from runtime.
`orchestration.bridge_contracts` exposes runtime-owned inventories and
retirement budgets used to audit the bridge. The distribution metadata and
console-script declaration remain local because PyPI installation and the
historical executable name are themselves compatibility surfaces.

## Navigate by consumer symptom

- An old Python import fails: locate the historical path, then its runtime
  target in the table above.
- The legacy command differs from the runtime command: inspect
  `interfaces.cli` and the package script entrypoint.
- A provider extra no longer resolves: compare the legacy optional dependency
  with the matching runtime extra.
- A bridge path appears to contain new behavior: treat that as ownership drift
  and move the implementation to runtime before extending it.

The compatibility inventory and tests are the behavioral evidence. Directory
size is not evidence of independent product ownership.
