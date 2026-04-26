---
title: Runtime Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-04-26
---

# Runtime Handbook

`bijux-proteomics-runtime` is the execution layer for the proteomics package
family. Open this handbook when you need to understand how work runs, how
operators and services invoke that work, and how runs remain inspectable and
reproducible. It does not own the scientific meaning of proteins, evidence,
scoring, or lab planning.

This page is for readers who need a fast, honest answer to three questions:

- what the runtime package owns
- what lower packages still own
- how migration from legacy `agentic-proteins` modules is being reviewed

The runtime is where the package family becomes executable for operators and
services. Lower packages define meaning, contracts, evidence, decisions, and
lab outcomes. Runtime composes those surfaces into runs, tracks artifacts and
state, and keeps the execution path inspectable enough to reproduce and review.

```mermaid
flowchart LR
    reader["reader question<br/>what turns proteomics logic into a real run?"]
    operator["operator or service request"]
    runtime["bijux-proteomics-runtime<br/>CLI, API, providers, replay, artifacts"]
    foundation["foundation<br/>shared schemas and primitives"]
    core["core<br/>biology, sequence, structure"]
    knowledge["knowledge<br/>evidence, confidence, trust"]
    intelligence["intelligence<br/>ranking, scoring, loop policy"]
    lab["lab<br/>experiment planning and promotion"]
    ledger["migration ledger<br/>legacy ownership review"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class reader page;
    class foundation,core,knowledge,intelligence,lab positive;
    class runtime anchor;
    class ledger caution;
    reader --> operator
    operator --> runtime
    runtime --> foundation
    runtime --> core
    runtime --> knowledge
    runtime --> intelligence
    runtime --> lab
    runtime -.reviews legacy placement through.-> ledger
```

## Start Here

- open [agentic-proteins](https://bijux.io/bijux-proteomics/02-agentic-proteins/) when the question
  starts from a legacy import or CLI path
- open [Repository Handbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/) when the runtime
  question is really about repository-wide migration or release rules
- open the published handbook pages below when you need runtime ownership,
  migration, or lower-package context

## What Runtime Owns

- operator entrypoints such as the CLI and HTTP API
- provider binding and provider execution adapters
- orchestration, state transitions, replay, and determinism controls
- runtime workspaces, run artifacts, and execution lifecycle handling

## What Runtime Must Not Absorb

- canonical domain models and biological semantics
- evidence, confidence, and contradiction semantics
- scoring, recommendation, and loop-policy semantics
- experiment-planning semantics and outcome-promotion semantics

Runtime composes lower packages through adapters. Lower packages should stay
runtime-agnostic.

## Open This Section When

- you need to understand why a behavior belongs in runtime instead of a lower
  package
- you are reviewing migration of legacy `agentic-proteins` modules
- you need the stable runtime ownership and contract references before editing
  code or docs

## Open Another Package When

- the real question already belongs to one lower package's biological,
  evidence, decision, or lab semantics
- you need repository automation detail rather than runtime behavior
- you are trying to preserve a legacy entrypoint without checking whether the
  canonical runtime surface already replaced it

## Concrete Anchors

- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/interfaces/cli.py`
  for operator entrypoints
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api/` for
  HTTP runtime surfaces
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/runtime/`
  for execution control, adapters, and workspaces
- `packages/bijux-proteomics-runtime/tests` for execution, API, provider, and
  compatibility proof

## Published Runtime References

- [Repository Runtime Migration Validation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/runtime-migration-validation/)
- [Foundation Handbook](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
- [Core Handbook](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
- [Intelligence Handbook](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
- [Knowledge Handbook](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
- [Lab Handbook](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)

## Migration Review Documents

- [Migration Ledger](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/migration-ledger/)
- [Agentic Module Ledger Summary](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-module-ledger-summary/)

## Bottom Line

Open this handbook when the unresolved question is how proteomics work becomes a
real run. Runtime should compose lower packages and make execution inspectable;
it should not quietly absorb the domain meaning that those packages already own.
