---
title: Agentic Module Ledger Summary
audience: maintainer
type: reference
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-04-26
---

# agentic-proteins Module Migration Ledger Summary

This summary gives maintainers a quick view of the current migration posture.
The important signal is not only how many modules exist, but where certainty is
already high and where review debt still sits.

```mermaid
flowchart TD
    total["148 legacy modules"]
    exec["54 runtime execution modules"]
    review["64 review-required modules"]
    domain["30 domain-owned modules"]
    runtime["117 target: bijux-proteomics-runtime"]
    core["12 target: bijux-proteomics-core"]
    intelligence["16 target: bijux-proteomics-intelligence"]
    knowledge["2 target: bijux-proteomics-knowledge"]
    compat["1 target: agentic-proteins-compat"]
    agents["largest review hotspot<br/>agents: 22"]
    legacycore["core helpers under review: 16"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    total --> exec
    total --> review
    total --> domain
    exec --> runtime
    review --> runtime
    review --> agents
    review --> legacycore
    domain --> core
    domain --> intelligence
    domain --> knowledge
    runtime --> compat
    class total page;
    class exec,domain,core,intelligence,knowledge,runtime positive;
    class review,agents,legacycore,compat caution;
```

## Current Counts

- total modules: 148
- `runtime_execution_ownership`: 54
- `runtime_support_internal_review`: 64
- `domain_ownership`: 30

About 36% of the ledger is already classified as clear runtime execution
ownership, about 43% still needs internal review, and about 20% is marked for
lower-layer domain ownership.

## Target Owner Distribution

- `bijux-proteomics-runtime`: 117
- `bijux-proteomics-intelligence`: 16
- `bijux-proteomics-core`: 12
- `bijux-proteomics-knowledge`: 2
- `agentic-proteins-compat`: 1

## Where Review Debt Concentrates

- `agents/**` is the largest review cluster with 22 modules
- legacy `core/**` helpers account for 16 review-required modules
- `execution/**` contributes 7 review-required modules that may still mix
  orchestration and domain validation concerns

## What The Numbers Mean

The migration is not blocked by uncertainty about the public runtime surface.
The strongest ambiguity sits in runtime-adjacent support code where older
modules still blend orchestration, validation, reporting, or agent behavior.

That is why the review bucket is larger than the clear domain bucket. The next
useful work is not broad renaming. It is narrowing mixed modules until each one
can be defended as either canonical runtime behavior or lower-layer domain
ownership.
