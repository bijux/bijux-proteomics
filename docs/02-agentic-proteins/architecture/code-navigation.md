---
title: Code Navigation
audience: developer
type: architecture
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Code Navigation

Agentic Proteins is a compatibility package over
`bijux-proteomics-runtime`. Its source tree deliberately resembles the earlier
agentic layout, but most modules now forward objects from their canonical
runtime owners. Read it as a migration map, not as an independent execution
engine.

## Fast reading route

1. Start at `agentic_proteins/__init__.py`. The root facade exposes only
   `AppConfig`, `RunManager`, `cli`, and `create_app`, loaded lazily from the
   runtime package.
2. For command or service behavior, move immediately to `interfaces/cli.py` or
   `interfaces/http/`. These are compatibility entrypoints over the runtime CLI,
   application, middleware, schemas, router, and versioned endpoints.
3. For run lifecycle, artifacts, validation, telemetry, or state, inspect
   `execution/` and `state/`, then follow the imported owner into runtime. The
   parallel `orchestration/` family exists for historical imports and resolves
   to the same canonical implementation.
4. For agents and tools, use `agents/` and `tools/` to locate the legacy import,
   then read the runtime owner for behavior. Catalogs, contracts, planning,
   verification, execution, and reporting are not reimplemented locally.
5. For structure providers, start at `providers/__init__.py`, then distinguish
   built-in heuristic, local, and remote providers. The `experimental/` family
   is a legacy alias to remote provider helpers.
6. Confirm the compatibility promise in package tests and the runtime behavior
   in `packages/bijux-proteomics-runtime/tests`.

## Question-to-owner map

| Question | Start in Agentic Proteins | Canonical owner |
| --- | --- | --- |
| How do I create the app or invoke the CLI? | root facade or `interfaces/` | runtime `api` |
| How is a run configured and finalized? | `execution/manager.py`, `execution/run_config.py` | runtime `runs` |
| How are agents planned and coordinated? | `agents/` | runtime `execution.agents` |
| How are tools registered and validated? | `tools/` | runtime `execution.tools` |
| How is provider capability selected? | `providers/` | runtime `providers` |
| How is state persisted or snapshotted? | `state/` | runtime `state` and `support.workspace` |
| Why does an old import still work? | matching compatibility module | runtime compatibility inventory and migration ledger |

## Read forwarding modules correctly

A one-line wildcard import is a compatibility statement, not missing
implementation. Do not search nearby Agentic Proteins modules for hidden
behavior; follow the imported runtime path. Modules with explicit `__all__`
lists narrow and document the legacy surface, while the package root is the
smallest supported facade.

When diagnosing a regression, first determine whether the legacy import failed
to forward or whether the canonical runtime behavior changed. The former
belongs here; the latter belongs in runtime. That distinction prevents fixes
from creating two execution implementations.
