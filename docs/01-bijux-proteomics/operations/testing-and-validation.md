---
title: Testing and Validation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Testing and Validation

Validation in `bijux-proteomics` is layered: packages protect their own
behavior, while the repository protects the seams between packages, schema
artifacts, docs, and release conventions.

```mermaid
flowchart TB
    pkg[package-local tests]
    api[API contract checks under apis/*/v1]
    docs[docs and metadata checks]
    wf[GitHub workflows]
    promise[prose promises]

    pkg --> api --> docs --> wf
    promise -. incomplete without .-> pkg
    promise -. incomplete without .-> docs
```

## Validation Layers

- package-local unit, integration, and invariant suites
- API contract checks under `apis/*/v1`
- docs, metadata, and repository checks in `bijux-proteomics-dev`
- repository workflows under `.github/workflows/`

## Validation Rule

A prose promise is incomplete until package tests or repository tooling can
detect its drift.

## Purpose

This page explains the relationship between package truth and repository truth.

## Stability

Keep it aligned with the current test layout and validation workflows.
