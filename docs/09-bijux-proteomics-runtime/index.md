---
title: Runtime Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-04-26
---

# Runtime Handbook

`bijux-proteomics-runtime` is the canonical execution package for the
proteomics family. It owns how work is invoked, orchestrated, replayed, and
made inspectable after the run. This is where the system becomes operational:
operators touch it, providers plug into it, state moves through it, and runs
leave artifacts behind that a reviewer can inspect later.

```mermaid
flowchart LR
    operators["operators<br/>CLI, HTTP, automation"]
    bridge["agentic-proteins<br/>legacy paths"]
    runtime["runtime<br/>orchestration and control"]
    providers["providers and tools"]
    state["state, memory, registry"]
    validation["validation and replay"]
    artifacts["run artifacts and execution record"]

    operators --> runtime
    bridge -. migrate .-> runtime
    runtime --> providers
    runtime --> state
    runtime --> validation
    validation --> artifacts
    providers --> artifacts
    state --> artifacts
```

## Why This Package Is Central

- it is the place where abstract package contracts become concrete runs
- it keeps execution reviewable instead of letting provider calls disappear into
  opaque side effects
- it holds the operational seam between the product family and the outside
  world

## Shared Reader Routes

- Use [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
  when the question is still about rerun flow rather than one runtime-owned
  surface.
- Use [Operator Rerun Journey](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operator-rerun-journey/)
  when the question starts from a flagship workflow family rather than from a
  runtime subsystem.

## Start Inside This Package

- open [Flagship Run Registry](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/flagship-run-registry/) when the question is which public benchmark runs are actually checked and what claims they authorize
- open [Benchmark Rerun Kits](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/benchmark-rerun-kits/) when the question is how to reopen a workflow family from its primary and companion package roots without maintainer narration
- open [Benchmark Comparability Matrix](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/benchmark-comparability-matrix/) when the question is whether a workflow sentence survives both the flagship package and the companion generalization package
- open [Black-Box Benchmark Dashboard](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/black-box-benchmark-dashboard/) when the question is whether current public workflow language is actually supported by the live rerun evidence
- open [Runtime Execution Boundary](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-execution-boundary/) when the question is how an independent reviewer would reopen a shipped workflow family from benchmark manifest to checked runtime bundle
- open [Black-Box Run Verification](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/black-box-run-verification/) when the question is which exact artifacts connect a public benchmark package to runtime bundle, stage lineage, and replay challenge
- open [Raw Versus Import Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/raw-versus-import-execution/) when the dispute is whether a workflow family currently earns raw-rerun language or still stops at imported evidence
- open [Runtime Replay Challenges](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-replay-challenges/) when the question is the smallest hostile rerun or invalidation challenge that should reconstruct the shipped runtime story
- open [Runtime Environment Contracts](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-environment-contracts/) when the question is which software and dependency combinations the shipped runtime lane actually supports
- open [Runtime Artifact Stability](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-artifact-stability/) when the question is what must remain bit-stable, value-stable, or review-stable across repeated reruns
- open [Runtime Rerun Refusals](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-rerun-refusals/) when the question is why a family still cannot be rerun more faithfully without overstating the current lane
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

- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api/cli.py`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api/`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/execution/`, `providers/`, and `state/`
- `packages/bijux-proteomics-runtime/tests`

## Migration References

- [Repository Runtime Migration Validation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/runtime-migration-validation/)
- [Migration Ledger](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/migration-ledger/)
- [Agentic Module Ledger Summary](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-module-ledger-summary/)

## Boundary

Runtime should explain execution clearly, but it should not quietly absorb the
meaning of evidence, recommendation, or lab intent just because those meanings
eventually move through a run.
