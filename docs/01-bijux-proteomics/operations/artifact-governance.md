---
title: Artifact Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Artifact Governance

Generated output is useful only when its status is obvious. The repository
needs a clean distinction between canonical source, tracked reference
artifacts, and disposable build output.

```mermaid
flowchart LR
    source["canonical source"]
    refs["tracked reference artifacts"]
    docs["checked docs and metadata"]
    generated["generated output under artifacts/"]
    policy["artifact governance"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    source --> policy
    refs --> policy
    docs --> policy
    policy --> generated
    class policy page;
    class source,refs,docs anchor;
    class generated action;
```

## Artifact Classes

- tracked API reference artifacts under `apis/`
- checked documentation and metadata files that participate in repository
  policy
- generated local or CI output under `artifacts/`

## Dependency Allowlist

The dependency allowlist used by `bijux_proteomics_dev.security.dependency_allowlist`
is recorded here so repository policy stays visible.

- requests
- biopython
- numpy
- click
- fastapi
- uvicorn
- pydantic
- loguru
- slowapi
- boto3

## Purpose

This page explains how the repository distinguishes durable reference artifacts
from generated workflow output.

## Stability

Update it when the repository meaning of a tracked artifact class changes.
