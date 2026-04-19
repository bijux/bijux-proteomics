---
title: Artifact Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Artifact Governance

Generated output is useful only when its status is obvious. The repository
needs a clean distinction between canonical source, tracked reference
artifacts, and disposable build output.

```mermaid
flowchart TD
    A[Repository artifacts] --> B[Tracked reference artifacts]
    A --> C[Checked docs / metadata]
    A --> D[Generated output]

    B --> B1[apis/]
    C --> C1[docs and governance files]
    D --> D1[artifacts/ local or CI output]

    E[Dependency allowlist] --> F[approved external packages]
    F --> F1[requests]
    F --> F2[biopython]
    F --> F3[numpy]
    F --> F4[click]
    F --> F5[fastapi]
    F --> F6[uvicorn]
    F --> F7[pydantic]
    F --> F8[loguru]
    F --> F9[slowapi]
    F --> F10[boto3]
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
