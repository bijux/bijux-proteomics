---
title: API and Schema Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# API and Schema Governance

Shared API artifacts live under `apis/` so contract review does not depend on
reverse-engineering Python modules. Code and tracked schema files should tell
one public story.

```mermaid
flowchart LR
    code["package public behavior"]
    schema["tracked schema in apis/*/v1"]
    pinned["pinned OpenAPI and digests"]
    drift["drift checks"]
    review["contract review"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    code --> schema --> pinned --> drift --> review
    class review page;
    class code,schema,pinned,drift anchor;
```

## Current Contract Roots

- `apis/bijux-proteomics-runtime/v1/` (canonical runtime API ownership)
- `apis/agentic-proteins/v1/` (compatibility mirror for legacy runtime path)
- `apis/bijux-proteomics-foundation/v1/`
- `apis/bijux-proteomics-core/v1/`
- `apis/bijux-proteomics-intelligence/v1/`
- `apis/bijux-proteomics-knowledge/v1/`
- `apis/bijux-proteomics-lab/v1/`

## Governance Rules

- package code and tracked schema files must describe the same public behavior
- pinned OpenAPI JSON and digests move only with reviewable intent
- schema drift checks belong in tooling and tests, not in prose alone

## Purpose

This page explains how repository-level API artifacts stay synchronized with
the code that claims to implement them.

## Stability

Keep it aligned with the real schema roots and drift checks under `apis/` and
`bijux-proteomics-dev`.
