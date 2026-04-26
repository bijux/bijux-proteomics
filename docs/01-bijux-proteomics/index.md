---
title: Repository Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Repository Handbook

Open this handbook for questions that no single package can answer on its own.
The root is not a sixth product package. It explains how the package family
fits together, which assets genuinely live above one package, and where
cross-package rules begin and end.

If a reader can answer their question honestly from one package handbook, they
should go there instead of staying here.

The root is a coordination layer, not a shadow owner of product behavior. The
repository exists to keep several package-level promises moving together
without letting the root quietly absorb domain, runtime, or lab semantics that
belong elsewhere.

```mermaid
flowchart LR
    reader["reader question<br/>is this rule shared or package-local?"]
    root["Repository Handbook<br/>root-owned guidance"]
    foundation["Foundation<br/>split, scope, language"]
    operations["Operations<br/>validation, release, review"]
    packages["Package handbooks<br/>owned behavior"]
    maintain["Maintainer handbook<br/>repo health automation"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    reader --> root
    root --> foundation
    root --> operations
    root --> packages
    root --> maintain
    class root page;
    class foundation,operations anchor;
    class packages,maintain positive;
```

## Start Here

- open [Foundation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/) when the question is why the package
  split exists or where authority changes hands
- open [Operations](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/) when the question is how repository
  work is validated, released, or reviewed
- move straight to a product handbook when the real issue is already local to
  one package boundary
- move to [Maintainer Handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/) when
  the concern is CI, workflow fan-out, generated docs checks, or release
  tooling

## Pages In Repository Handbook

- [Foundation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/)
- [Operations](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/)

## What This Handbook Owns

- the shared explanation of why the root exists at all
- repository-wide workflow, validation, release, and artifact rules
- the seams where one package hands responsibility to another

## What This Handbook Does Not Own

- runtime execution behavior, provider semantics, or replay authority
- foundation, core, intelligence, knowledge, or lab behavior inside those
  package docs
- maintainer-helper implementation detail that belongs in the maintainer
  handbook

## Use This Handbook When

- questions about why the repository is split the way it is
- questions about root-managed assets such as `apis/`, `Makefile`, shared CI,
  and release conventions
- questions about where the root should stop and a product package should take
  over

## Move On When

- the answer lives mostly in one package's source tree, tests, or public
  surface
- the question is about one package's internal boundary rather than repository
  fit
- you are tempted to describe behavior at the root that really belongs inside
  `packages/`

## Package Handbooks

- [agentic-proteins](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/)
- [bijux-proteomics-foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/)
- [bijux-proteomics-core](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/)
- [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/)
- [bijux-proteomics-knowledge](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/)
- [bijux-proteomics-lab](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/)

## Concrete Anchors

- `pyproject.toml` for workspace metadata and package declarations
- `Makefile` and `makes/` for root automation and release routing
- `apis/` and `.github/workflows/` for schema and validation review
- `packages/` for the product boundaries this handbook must not blur

## Reader Takeaway

The job of this handbook is simple: help readers understand the system without
letting the root pretend it owns behavior that belongs elsewhere. If the
current question can be answered honestly inside one product handbook, this
root should route you there instead of trying to keep you.
