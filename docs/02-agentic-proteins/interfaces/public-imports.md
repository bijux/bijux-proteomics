---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Public imports

The supported `agentic_proteins` namespace is a compatibility surface. New
applications use `bijux_proteomics_runtime`; existing callers can use the paths
below only within their documented forwarding contract.

## Canonical top-level migration

| Historical import | Canonical import | Guarantee |
| --- | --- | --- |
| `agentic_proteins.AppConfig` | `bijux_proteomics_runtime.AppConfig` | object identity |
| `agentic_proteins.RunManager` | `bijux_proteomics_runtime.RunManager` | object identity |
| `agentic_proteins.cli` | `bijux_proteomics_runtime.cli` | object identity |
| `agentic_proteins.create_app` | `bijux_proteomics_runtime.create_app` | object identity |

```python
from bijux_proteomics_runtime import AppConfig, RunManager
```

Use the canonical form in new code. The historical form remains relevant only
for callers covered by compatibility evidence.

## Nested namespace status

| Namespace | Compatibility purpose | Canonical authority |
| --- | --- | --- |
| `interfaces` | legacy CLI, HTTP, and structure-report entry points | Runtime interfaces |
| `execution` and `orchestration` | historical run, graph, artifact, telemetry, and validation paths | Runtime execution and runs |
| `state` | context, request, lifecycle, snapshot, output, and workspace imports | Runtime state |
| `providers` | local, remote, experimental, capability, and selection paths | Runtime providers |
| `agents` and `tools` | historical contracts, catalogs, planning, coordination, and verification paths | Runtime execution |

Nested paths are not covered by the four top-level identity assertions merely
because they share a package. Consult the relevant bridge contract and direct
comparison test before depending on one.

## Import rules

- importing the base package must not activate optional providers or network
  clients;
- legacy and canonical imports must preserve the documented identity or public
  behavior, including failures and artifacts;
- a compatibility import must not become the only decoder for durable Runtime
  state;
- no canonical package may import `agentic_proteins`; and
- removal requires a canonical replacement and evidence for affected callers.

The tracked API roots are `apis/agentic-proteins/v1` for compatibility and
`apis/bijux-proteomics-runtime/v1` for the canonical owner. The
[compatibility contract](../foundation/compatibility-contract.md) defines the
promise; [known limitations](../quality/known-limitations.md) defines its
current ceiling.
