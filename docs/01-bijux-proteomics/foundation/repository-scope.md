---
title: Repository Scope
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Repository Scope

The root should stay boring in the best possible way. When repository files
start absorbing product behavior, every package boundary becomes harder to
trust.

```mermaid
flowchart LR
    rootChange["proposed root change"]
    root["repository scope"]
    root1["shared docs and governance"]
    root2["checked API artifacts"]
    root3["CI and release coordination"]
    pkg1["package-local behavior"]
    pkg2["package internals"]
    pkg3["undocumented shortcuts"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    rootChange --> root
    root --> root1
    root --> root2
    root --> root3
    root -.keep in package.-> pkg1
    root -.keep in package.-> pkg2
    root -.reject.-> pkg3
    class root page;
    class root1,root2,root3 positive;
    class pkg1,pkg2,pkg3 caution;
```

## In Scope

- workspace-level automation and shared validation
- root handbook structure and repository-wide governance
- checked API artifacts under `apis/`
- release, docs, and CI rules that genuinely span packages

## Out Of Scope

- package-local runtime behavior
- quiet root helpers that bypass package APIs
- undocumented exceptions to the package ownership model

## Purpose

This page shows what the repository root is allowed to own.

## Stability

Keep it aligned with the current division between repository governance and
package-owned behavior.
