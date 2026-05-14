---
title: Ownership Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Ownership Model

The repository is easiest to review when ownership can be stated in layers
without hesitation. The root owns only what genuinely crosses package
boundaries. Six real product packages own publishable behavior. One explicit
compatibility bridge preserves legacy imports while callers migrate off old
paths. The maintainer package owns repository-health automation.

## Ownership Model

```mermaid
flowchart TB
    root["root docs, release framing, tracked artifacts, validation coordination"]
    maintain["bijux-proteomics-dev owns repository-health automation"]
    product["canonical packages own publishable behavior"]
    bridge["agentic-proteins owns temporary runtime forwarding"]

    root --> maintain
    root --> product
    product --> bridge
```

This page should make the ownership layers easy to state in one breath. If a reviewer has to improvise who owns a behavior, the repository has already lost clarity.

## Ownership Layers

- root docs, shared release framing, schema storage, and repository-wide
  validation coordination belong to the repository handbook and root surfaces
- repository-health helper code belongs in `bijux-proteomics-dev`
- canonical product behavior belongs in the publishable package that exposes it
- runtime compatibility forwarding belongs in `agentic-proteins` only while
  callers still depend on legacy paths

## Boundary Example

A new OpenAPI artifact under `apis/` is not automatically a root-owned feature.
The root may own how the artifact is tracked and validated, but the package that
exposes the API still owns what the API means. Root process and package meaning
must move together without becoming the same thing.

## First Proof Check

- `configs/package-governance/public-root-symbol-owners.toml` for the canonical
  package-root ownership map
- `packages/` for the product boundary
- `packages/bijux-proteomics-dev/` for maintainer automation
- root files such as `Makefile`, `apis/`, and `.github/workflows/` when the
  change truly spans more than one package

## Design Pressure

The common drift is to describe several layers correctly in isolation while still letting one change claim authority from two or three of them at once.
