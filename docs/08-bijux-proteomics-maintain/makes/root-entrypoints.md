---
title: Root Entrypoints
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Root Entrypoints

Root entrypoints are the command names maintainers and CI touch first. They should stay small, obvious, and easy to trace.

## Entrypoint Model

```mermaid
flowchart TB
    command["make <target>"]
    root["Makefile entrypoint"]
    next["next owning fragment obvious after one jump"]
    trace["maintainer can trace the command quickly"]

    command --> root
    root --> next
    next --> trace
```

This page should make the root entrypoints feel intentionally shallow. A top-level target is only healthy when it points a maintainer toward the next owning file without detective work.

## Entry Rules

- keep top-level targets readable from `Makefile`
- route shared behavior into named fragments rather than inline shell complexity
- make the next owning file obvious after one jump

## First Proof Check

- `Makefile`
- `makes/root.mk`

## Design Pressure

The easy failure is to keep root targets readable at the command line while hiding too much of the real behavior behind one opaque jump.
