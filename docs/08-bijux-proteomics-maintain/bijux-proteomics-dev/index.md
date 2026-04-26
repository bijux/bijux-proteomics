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

This package reduces mystery instead of creating more of it. If maintainer
logic cannot be explained from this section, the repository is relying too
heavily on implicit CI behavior.

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

## Pages In This Handbook

- [Package Overview](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/scope-and-non-goals/)
- [Module Map](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/module-map/)
- [Quality Gates](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/quality-gates/)
- [Security Gates](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/security-gates/)
- [Schema Governance](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/schema-governance/)
- [Release Support](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/release-support/)
- [Documentation Integrity](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/documentation-integrity/)
- [Operating Guidelines](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/operating-guidelines/)

## Open This Section When

- the issue is implemented as maintainer helper code under
  `packages/bijux-proteomics-dev/`
- you need to know which helper module or policy surface enforces a repository
  rule
- the concern is about schema drift, docs integrity, release support, security,
  or quality gates

## Open Another Section When

- the real question is about one product package API, CLI, runtime rule, or
  domain contract
- the issue belongs to shared Make routing or GitHub Actions trigger logic
- you are looking for end-user behavior rather than repository-health helpers

## Choose A Page

- open [Package Overview](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/package-overview/) for the shortest statement of why
  this maintainer package exists
- open [Module Map](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/module-map/) when you need the helper-module layout
- open [Quality Gates](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/quality-gates/), [Security Gates](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/security-gates/),
  or [Documentation Integrity](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/documentation-integrity/) when the issue is a
  policy check
- open [Schema Governance](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/schema-governance/) or
  [Release Support](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/release-support/) when the issue is publication-facing

## Reader Takeaway

Open `bijux-proteomics-dev` when repository-health behavior is implemented as
helper code. If the question is really about shared command routing or
workflow entrypoints, open `makes/` or `gh-workflows/` instead.

## What You Get

This page gives you the fastest route from a repository-health rule to the
helper package page that explains the owning module or policy surface.
