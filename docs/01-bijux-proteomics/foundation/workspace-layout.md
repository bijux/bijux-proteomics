---
title: Workspace Layout
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Workspace Layout

The top-level tree should help readers place work quickly. If the layout makes
ownership harder to see, it is working against the design.

```mermaid
flowchart TB
    repo[bijux-proteomics]
    repo --> packages[packages/]
    repo --> apis[apis/]
    repo --> docs[docs/]
    repo --> makes[makes/ + Makefile]
    repo --> configs[configs/]
    repo --> artifacts[artifacts/]

    packages --> p1[publishable distributions]
    packages --> p2[maintainer tooling]
    apis --> a1[schema sources]
    apis --> a2[pinned OpenAPI + digests]
    docs --> d1[canonical handbook]
    makes --> m1[shared automation]
    configs --> c1[tool config]
    artifacts --> r1[generated output only]
```

## Top-Level Directories

- `packages/` for publishable Python distributions and maintainer tooling
- `apis/` for checked schema sources, pinned OpenAPI JSON, and digests
- `docs/` for the canonical handbook
- `makes/` and `Makefile` for repository automation
- `configs/` for shared tool configuration
- `artifacts/` for generated validation output

## Layout Rule

A concern should live at the root only when it serves more than one package or
when it explains the workspace itself.

## Purpose

This page explains the top-level directory split that supports the repository
ownership model.

## Stability

Keep it aligned with the real top-level directories and their current meaning.
