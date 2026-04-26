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

This section should make one distinction obvious: root operations exist to
coordinate the repository as a whole, not to re-describe package-local runtime,
evidence, or lab procedures that already have their own handbooks.

```mermaid
flowchart LR
    reader["reader question<br/>which root-owned workflow governs this work?"]
    setup["local setup and contributor flow"]
    validation["shared validation,<br/>schema governance, migration checks"]
    release["release, automation,<br/>artifact, and review posture"]
    rootops["root-owned operations<br/>repeatable repository workflows"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    class reader page;
    class setup,validation,release,rootops positive;
    reader --> rootops
    rootops --> setup
    rootops --> validation
    rootops --> release
```

## Start Here

- open [Local Development](local-development.md) when the concern is repeatable
  local setup and contributor flow
- open [Testing and Validation](testing-and-validation.md) or
  [Runtime Migration Validation](runtime-migration-validation.md) when the
  issue is repository-wide proof rather than one package test
- open [Release and Versioning](release-and-versioning.md) or
  [Automation Surfaces](automation-surfaces.md) when the concern is publication
  or root-owned automation
- open [Review Expectations](review-expectations.md) when the real question is
  what evidence and scope discipline a root-level change needs

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

## What This Section Clarifies

- which workflows are genuinely root-owned and therefore cannot be documented
  honestly by any one package
- where setup, validation, release, and review expectations are governed above
  package level
- when the right answer is to leave the root handbook and drop into a package
  handbook instead

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

## Concrete Anchors

- `Makefile` and `makes/` for root-owned command routing
- `.github/workflows/` for automation surfaces discussed from the repository
  point of view
- `packages/bijux-proteomics-dev/` for helper-code enforcement that supports
  these root workflows
- `docs/01-bijux-proteomics/operations/` for the checked-in process pages this
  section is routing to

## Reader Takeaway

This section is for root-owned operational behavior that no single package can
document honestly on its own. It should help readers find the governing process
quickly without letting the repository root pretend it owns package behavior.
