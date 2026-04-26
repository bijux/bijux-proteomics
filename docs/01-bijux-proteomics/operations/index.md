---
title: Operations
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Operations

The operations section explains how the repository is run, reviewed, and kept
coherent after the ownership model is already clear.

These pages are about repeatable repository work rather than package-local
behavior. They should help a maintainer move from a question about setup,
validation, release flow, automation, or review posture to the checked-in files
that carry that work today.

```mermaid
flowchart LR
    work1["local development and contributors"]
    work2["validation, release, and governance"]
    work3["automation, artifacts, and review"]
    ops["Repository operations<br/>repeatable root workflows"]
    next1["workflow pages"]
    next2["migration validation"]
    next3["review expectations"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    work1 --> ops
    work2 --> ops
    work3 --> ops
    ops --> next1
    ops --> next2
    ops --> next3
    class ops page;
    class work1,work2,work3 positive;
    class next1,next2,next3 anchor;
```

## Pages In This Section

- [Local Development](local-development.md)
- [Testing and Validation](testing-and-validation.md)
- [Release and Versioning](release-and-versioning.md)
- [API and Schema Governance](api-and-schema-governance.md)
- [Runtime Migration Validation](runtime-migration-validation.md)
- [Contributor Workflows](contributor-workflows.md)
- [Automation Surfaces](automation-surfaces.md)
- [Artifact Governance](artifact-governance.md)
- [Review Expectations](review-expectations.md)
- [Change Management](change-management.md)

## Use This Section When

- the question is about repository-wide setup, validation, release posture,
  shared automation, or review rules
- the answer should come from root-owned workflows rather than one product
  package handbook
- you need to know which checked-in operational page owns a shared process

## Do Not Start Here When

- the concern is really about one package's internal contract, API, or runtime
  behavior
- the question can already be answered honestly from a single package handbook
- you are looking for maintainer helper implementation details rather than root
  repository process

## Choose The Next Page By Question

- open [Local Development](local-development.md) or
  [Testing and Validation](testing-and-validation.md) when the concern is
  repeatable local work
- open [Release and Versioning](release-and-versioning.md) or
  [API and Schema Governance](api-and-schema-governance.md) when the concern is
  publication or contract discipline
- open [Contributor Workflows](contributor-workflows.md),
  [Automation Surfaces](automation-surfaces.md), or
  [Review Expectations](review-expectations.md) when the concern is shared team
  process

## Reader Takeaway

This section is for root-owned operational behavior that no single package can
document honestly on its own. It should help readers find the governing process
quickly without letting the repository root pretend it owns package behavior.

## Purpose

This page gives maintainers the shortest route into repository-wide operational
guidance.

## Stability

Keep it aligned with the operational topics that actually matter at the root.
