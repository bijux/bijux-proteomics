---
title: Contributor Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Contributor Workflows

Contributors can move through the repository in a repeatable
order.

```mermaid
flowchart LR
    read["read the relevant handbook page"]
    edit["make the owned change"]
    route["package-local or root-level?"]
    proof["update docs, schemas, and tests"]
    review["submit coherent review unit"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    read --> edit --> route --> proof --> review
    class review page;
    class read,edit,route,proof anchor;
```

## Common Workflow Shape

- start in the relevant handbook section before editing shared files
- make package-local changes in the owning package when behavior is local
- use root automation when the work spans docs, schemas, release flow, or more
  than one package
- update explanation and proof in the same change series

## Purpose

This page shows the normal repository workflow shape so shared work requires
less guesswork.

## Stability

Update it when the checked-in contributor path really changes.
