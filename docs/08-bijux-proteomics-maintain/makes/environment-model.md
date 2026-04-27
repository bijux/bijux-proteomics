---
title: Environment Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Environment Model

Environment handling should make local and CI execution reproducible without hiding required assumptions.

## Environment Model

```mermaid
flowchart TB
    input["local or CI invocation"]
    env["shared environment fragments"]
    override["package-specific overrides stay visible"]
    assumption["required tooling assumptions fail early"]
    run["command runs reproducibly"]

    input --> env
    env --> override
    override --> assumption
    assumption --> run
```

This page should make environment handling feel like explicit setup logic rather than implicit shell state. Reproducibility depends on visible assumptions, not on lucky machine parity.

## Environment Rules

- centralize shared environment logic in dedicated fragments
- keep package-specific overrides visible
- fail early when required tooling assumptions are missing

## First Proof Check

- `makes/env.mk`
- env-related includes under `makes/bijux-py/`

## Design Pressure

The easy failure is to make environment handling feel smooth by hiding assumptions until they break differently on another machine or in CI.
