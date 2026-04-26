---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-foundation` exists to stabilize shared payload meaning through identifiers, schema compatibility, migrations, and deterministic serialization. The package is useful only when that
role stays narrow enough that a reviewer can say why it exists without naming
several different owners at once.

## What It Owns

- define shared identifiers
- govern schema and serialization compatibility
- carry migration helpers for payload evolution

## What It Refuses

- program policy
- evidence truth and contradictions
- execution orchestration

## First Proof Check

- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation`
- `packages/bijux-proteomics-foundation/tests`
- neighboring handbook branches once a change crosses the local role
