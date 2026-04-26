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
family. It owns how work runs, how operators and services invoke that work, and
how runs remain inspectable and reproducible. It does not own the scientific
meaning of proteins, evidence, scoring, or lab planning.

This section is for readers who need a clear answer to three questions:

- what the runtime package owns
- what lower packages still own
- how migration from legacy `agentic-proteins` modules is being reviewed

```mermaid
flowchart LR
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
    class operator,page runtime;
    class foundation,core,knowledge,intelligence,lab positive;
    class ledger caution;
    operator --> runtime
    runtime --> foundation
    runtime --> core
    runtime --> knowledge
    runtime --> intelligence
    runtime --> lab
    runtime -.reviews legacy placement through.-> ledger
```

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

## Use This Section When

- you need to understand why a behavior belongs in runtime instead of a lower
  package
- you are reviewing migration of legacy `agentic-proteins` modules
- you need the stable runtime ownership and contract references before editing
  code or docs

## Source Package Documents

- [Architecture](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-runtime/docs/ARCHITECTURE.md)
- [Boundaries](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-runtime/docs/BOUNDARIES.md)
- [Contracts](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-runtime/docs/CONTRACTS.md)

## Migration Review Documents

- [Migration Ledger](migration-ledger/README.md)
- [Agentic Module Ledger Summary](migration-ledger/agentic-proteins-module-ledger-summary.md)
