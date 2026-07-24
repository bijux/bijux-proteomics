---
title: Compatibility Contract
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Compatibility Contract

`agentic-proteins` preserves established access to canonical
`bijux-proteomics-runtime` behavior. Compatibility is observable parity, not
similar intent: consumers should see the same objects, inputs, outputs,
failures, and lifecycle through supported historical paths.

## Supported Root Contract

| Historical name | Canonical owner |
| --- | --- |
| `agentic_proteins.AppConfig` | `bijux_proteomics_runtime.AppConfig` |
| `agentic_proteins.RunManager` | `bijux_proteomics_runtime.RunManager` |
| `agentic_proteins.cli` | `bijux_proteomics_runtime.cli` |
| `agentic_proteins.create_app` | `bijux_proteomics_runtime.create_app` |

The root resolves lazily to Runtime and preserves object identity. Supported
nested paths are governed separately in [Public Imports](../interfaces/public-imports.md)
and the compatibility inventory; source-tree presence alone is not a promise.

## Observable Parity

| Surface | Parity requirement |
| --- | --- |
| Python import | same canonical object or explicitly documented adapter |
| callable | signature, defaults, return type, exceptions, and side effects |
| model | validation, serialization, schema, and migration behavior |
| CLI | command names, options, help, exit status, output, and artifacts |
| HTTP | route inventory, request/response schema, middleware, dependencies, and errors |
| lifecycle | state transitions, replay, cancellation, refusal, and recovery |

Version equality alone does not prove parity. A forwarding package can install
successfully while pointing at a missing symbol, changed default, or divergent
error contract.

## Failure Contract

Unsupported historical paths fail explicitly. They must not fall back to
copied implementations, dynamically guess a replacement, or import an internal
Runtime path that is absent from the public ledger. Optional Runtime
dependencies retain their canonical unavailable or degraded behavior.

## Migration And Retirement

Consumers migrate by replacing supported `agentic_proteins` paths with the
corresponding Runtime owner paths and running behavior-level tests. Retirement
requires:

1. a complete supported-path inventory;
2. replacement guidance and release communication;
3. observed consumer migration or an explicit support-ending decision;
4. parity evidence through the final supported release; and
5. coordinated removal from distribution metadata, CLI, HTTP, docs, and tests.

Until those conditions hold, the bridge remains supported but non-canonical.
New integrations should import Runtime directly.
