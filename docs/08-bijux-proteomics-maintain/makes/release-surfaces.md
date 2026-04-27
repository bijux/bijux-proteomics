---
title: Release Surfaces
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Release Surfaces

Release surfaces are where local commands and publication workflows meet. They deserve explicit routing and explicit failure points.

## Release Model

```mermaid
flowchart TB
    local["local release-oriented command"]
    publish["publish fragments"]
    workflow["release workflow stage"]
    failure["explicit proof or failure point"]

    local --> publish
    publish --> workflow
    workflow --> failure
```

This page should make release targets feel like controlled publication gates rather than convenience shortcuts. The command surface is only safe while each release step still has an obvious proof point.

## Release Rules

- keep publication targets easy to trace from the root surface
- align make release targets with workflow release stages
- treat release shortcuts that skip proof as defects

## First Proof Check

- `makes/publish.mk`
- release workflow files under `.github/workflows/`

## Design Pressure

The easy failure is to add a release shortcut that feels efficient locally but quietly skips the proof a workflow would have enforced.
