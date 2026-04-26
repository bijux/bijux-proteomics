---
title: bijux-proteomics-dev
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-dev

`bijux-proteomics-dev` is the repository maintenance package. It owns the
checked-in tooling that keeps docs, schema contracts, release metadata,
security policy, and repository automation honest across the package family.

This package should reduce mystery, not create more of it. If maintainer logic
cannot be explained from this section, the repository is relying too heavily on
implicit CI behavior.

```mermaid
flowchart LR
    dev["bijux-proteomics-dev"]
    quality["quality gates"]
    security["security and policy checks"]
    schema["schema and docs integrity"]
    release["release support"]
    reader["reader question<br/>which helper surface owns this rule?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class dev,page reader;
    class quality,security,schema,release positive;
    dev --> quality
    dev --> security
    dev --> schema
    dev --> release
    dev --> reader
```

## Pages In This Section

- [Package Overview](package-overview.md)
- [Scope and Non-Goals](scope-and-non-goals.md)
- [Module Map](module-map.md)
- [Quality Gates](quality-gates.md)
- [Security Gates](security-gates.md)
- [Schema Governance](schema-governance.md)
- [Release Support](release-support.md)
- [Documentation Integrity](documentation-integrity.md)
- [Operating Guidelines](operating-guidelines.md)

## Use This Section When

- the issue is implemented as maintainer helper code under
  `packages/bijux-proteomics-dev/`
- you need to know which helper module or policy surface enforces a repository
  rule
- the concern is about schema drift, docs integrity, release support, security,
  or quality gates

## Do Not Use This Section When

- the real question is about one product package API, CLI, runtime rule, or
  domain contract
- the issue belongs to shared Make routing or GitHub Actions trigger logic
- you are looking for end-user behavior rather than repository-health helpers

## Choose The Next Page By Question

- open [Package Overview](package-overview.md) for the shortest statement of why
  this maintainer package exists
- open [Module Map](module-map.md) when you need the helper-module layout
- open [Quality Gates](quality-gates.md), [Security Gates](security-gates.md),
  or [Documentation Integrity](documentation-integrity.md) when the issue is a
  policy check
- open [Schema Governance](schema-governance.md) or
  [Release Support](release-support.md) when the issue is publication-facing

## Reader Takeaway

Use `bijux-proteomics-dev` when repository-health behavior is implemented as
helper code. If the question is really about shared command routing or workflow
entrypoints, move sideways to `makes/` or `gh-workflows/` instead.

## Purpose

This page gives maintainers a stable overview of the package that owns
repository-health automation.

## Stability

Keep it aligned with the actual maintainer package responsibilities under
`packages/bijux-proteomics-dev/`.
