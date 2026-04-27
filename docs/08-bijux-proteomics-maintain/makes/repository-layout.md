---
title: Repository Layout
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Repository Layout

Make routing reflects repository layout. If the layout and the targets drift apart, maintainer work becomes guesswork.

## Layout Model

```mermaid
flowchart TB
    layout["repository layout"]
    shared["shared fragments"]
    package["package fragments"]
    names["target names follow real boundaries"]
    routing["dispatch stays guessable"]

    layout --> shared
    layout --> package
    shared --> names
    package --> names
    names --> routing
```

This page should show why repository layout matters to the make layer: target names and fragment boundaries are easier to audit when they mirror real ownership.

## Layout Rules

- shared repository targets stay in shared fragments
- package-specific rules stay under `makes/packages/`
- keep naming aligned with real repository and package boundaries

## First Proof Check

- `makes/`
- `makes/packages/`

## Design Pressure

The common drift is to let target organization follow historical convenience even after the repository layout and ownership model have changed underneath it.
