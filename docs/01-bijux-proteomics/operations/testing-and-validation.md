---
title: Testing and Validation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Testing and Validation

Validation in `bijux-proteomics` is layered: packages protect their own
behavior, while the repository protects the seams between packages, schema
artifacts, docs, and release conventions.

```mermaid
flowchart LR
    pkg["package-local tests"]
    api["API and schema checks"]
    docs["docs and metadata checks"]
    ci["repository workflows"]
    confidence["release confidence"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    pkg --> api --> docs --> ci --> confidence
    class confidence page;
    class pkg,api,docs,ci anchor;
```

## Validation Layers

- package-local unit, integration, and invariant suites
- API contract checks under `apis/*/v1`
- docs, metadata, and repository checks in `bijux-proteomics-dev`
- repository workflows under `.github/workflows/`

## Validation Rule

A prose promise is incomplete until package tests or repository tooling can
detect its drift.

