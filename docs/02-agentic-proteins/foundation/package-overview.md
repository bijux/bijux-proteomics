---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Package Overview

`agentic-proteins` exists to preserve legacy runtime imports and entrypoints while callers migrate to the canonical runtime package. The package is useful only when that
role stays narrow enough that a reviewer can say why it exists without naming
several different owners at once.

## What It Owns

- preserve legacy import paths
- preserve legacy CLI and API entry surfaces
- route readers and callers to the canonical runtime package

## What It Refuses

- new canonical runtime behavior
- new evidence or scoring semantics
- maintainer-only repository automation

## First Proof Check

- `packages/agentic-proteins/src/agentic_proteins`
- `packages/agentic-proteins/tests`
- neighboring handbook branches once a change crosses the local role
