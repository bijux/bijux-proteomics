---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-04
---

# Interfaces

This section explains the surfaces `bijux-proteomics-knowledge` is prepared to
support over time.

The package is library-first. The dependable interfaces are import contracts and
data shapes, not a packaged CLI or HTTP service.

## Visual Summary

```mermaid
flowchart LR
    imports["public imports in __init__.py"]
    schemas["schema and serialization contracts"]
    models["evidence/claims/resolution models"]
    tests["package tests for compatibility pressure"]
    imports --> tests
    schemas --> tests
    models --> tests
```

## Pages in This Section

- [CLI Surface](cli-surface.md)
- [API Surface](api-surface.md)
- [Configuration Surface](configuration-surface.md)
- [Data Contracts](data-contracts.md)
- [Artifact Contracts](artifact-contracts.md)
- [Entrypoints and Examples](entrypoints-and-examples.md)
- [Operator Workflows](operator-workflows.md)
- [Public Imports](public-imports.md)
- [Compatibility Commitments](compatibility-commitments.md)

## Read Across the Package

- [Foundation](../foundation/index.md) when you need the package boundary and ownership story first
- [Architecture](../architecture/index.md) when the question becomes structural, modular, or execution-oriented
- [Operations](../operations/index.md) when the question becomes procedural, environmental, diagnostic, or release-oriented
- [Quality](../quality/index.md) when the question becomes proof, risk, trust, or review sufficiency

## Concrete Anchors

- `src/bijux_proteomics_knowledge/__init__.py` for public import exports
- `src/bijux_proteomics_knowledge/schema.py` for schema compatibility contracts
- `src/bijux_proteomics_knowledge/serialization.py` for canonical serialization rules
- `src/bijux_proteomics_knowledge/evidence.py` and `claims.py` for core data surfaces

## Use This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Interfaces` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What This Page Answers

- which import paths and payload shapes callers can rely on
- where compatibility pressure is highest when models evolve
- what should trigger explicit compatibility review

## Reviewer Lens

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Honesty Boundary

This page can identify the intended public surfaces of `bijux-proteomics-knowledge`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Next Checks

- move to operations when the caller-facing question becomes procedural or environmental
- move to quality when compatibility or evidence of protection becomes the real issue
- move back to architecture when a public-surface question reveals a deeper structural drift

## Purpose

This page explains how to use the interfaces section for `bijux-proteomics-knowledge` without repeating the detail that belongs on the topic pages beneath it.

## Stability

This page is part of the canonical package docs spine. Keep it aligned with the current package boundary and the topic pages in this section.
