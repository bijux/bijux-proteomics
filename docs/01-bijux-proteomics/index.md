---
title: Repository Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Repository Handbook

This section is for the questions that no single package can answer on its
own. The root is not a sixth product package. It is where we explain how the
package family fits together, which assets genuinely live above one package,
and where cross-package rules begin and end.

If a reader can answer their question honestly from one package handbook, they
should go there instead of staying here.

```mermaid
flowchart LR
    questions["cross-package questions"]
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
    questions --> root
    root --> foundation
    root --> operations
    root --> packages
    root --> maintain
    class root page;
    class foundation,operations anchor;
    class packages,maintain positive;
```

## Handbook Sections

- [Foundation](foundation/index.md)
- [Operations](operations/index.md)

## What This Section Covers

- the package split and repository ownership model
- shared automation, validation, release, and review guidance
- the root-level rules that no one package can explain honestly on its own

## Use This Section For

- Questions about why the repository is split the way it is.
- Questions about root-managed assets such as `apis/`, `Makefile`, shared CI,
  and release conventions.
- Questions about where the root should stop and a product package should take
  over.

## Leave This Section For A Package Handbook When

- the answer lives mostly in one package's source tree, tests, or public surface
- the question is about one package's internal boundary rather than repository fit
- you are tempted to describe behavior at the root that really belongs inside
  `packages/`

## Package Handbooks

- [agentic-proteins](../02-agentic-proteins/foundation/index.md)
- [bijux-proteomics-foundation](../03-bijux-proteomics-foundation/foundation/index.md)
- [bijux-proteomics-core](../04-bijux-proteomics-core/foundation/index.md)
- [bijux-proteomics-intelligence](../05-bijux-proteomics-intelligence/foundation/index.md)
- [bijux-proteomics-knowledge](../06-bijux-proteomics-knowledge/foundation/index.md)
- [bijux-proteomics-lab](../07-bijux-proteomics-lab/foundation/index.md)

The job of this section is simple: help readers understand the system without
letting the root pretend it owns behavior that belongs elsewhere.
