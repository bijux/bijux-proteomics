---
title: Contributor Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Contributor Workflows

Contributors should be able to move through the repository in a repeatable
order.

```mermaid
flowchart TB
    subgraph Contributor
        start[Read relevant handbook page]
        edit[Make owned change]
        docs[Update explanation]
    end

    subgraph Repository
        root[root automation when work spans packages]
        proof[Tests/schemas/docs move together]
    end

    start --> edit
    edit -->|cross-package| root
    edit -->|package-local| docs
    root --> proof
    docs --> proof
```

## Common Workflow Shape

- start in the relevant handbook section before editing shared files
- make package-local changes in the owning package when behavior is local
- use root automation when the work spans docs, schemas, release flow, or more
  than one package
- update explanation and proof in the same change series

## Purpose

This page records the normal repository workflow shape so shared work requires
less guesswork.

## Stability

Update it when the checked-in contributor path really changes.
