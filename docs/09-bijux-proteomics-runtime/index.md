---
title: Runtime Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-04-26
---

# Runtime Handbook

`bijux-proteomics-runtime` is the canonical execution package for the proteomics family. It owns how work is invoked, orchestrated, replayed, and made inspectable after the run. It does not own biological meaning, evidence truth, recommendation policy, or lab-planning semantics.

## Start With

- open [agentic-proteins](https://bijux.io/bijux-proteomics/02-agentic-proteins/) when the question starts from a legacy import, CLI path, or API surface
- open [Migration Ledger](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/migration-ledger/) when the question is whether a legacy module still belongs in runtime ownership
- open the lower package handbooks when the disputed behavior is really domain, evidence, recommendation, or lab meaning

## What Runtime Owns

- operator entrypoints such as CLI and HTTP surfaces
- provider binding, execution adapters, and workspace control
- run orchestration, replay, determinism, and state transitions
- runtime artifacts and execution-lifecycle records

## What Runtime Refuses

- canonical domain and biology semantics
- evidence, confidence, contradiction, and review semantics
- recommendation policy, scoring, and design-loop meaning
- planning and outcome-promotion meaning from the lab layer

## First Proof Check

- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/interfaces/cli.py`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api/`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/runtime/`, `providers/`, and `validation/`
- `packages/bijux-proteomics-runtime/tests`

## Migration References

- [Repository Runtime Migration Validation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/runtime-migration-validation/)
- [Migration Ledger](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/migration-ledger/)
- [Agentic Module Ledger Summary](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-module-ledger-summary/)
