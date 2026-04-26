---
title: CI Targets
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# CI Targets

CI targets should mirror repository proof rules closely enough that local runs and workflow runs mean the same thing.

## CI Rules

- keep CI-oriented targets explicit and reusable
- align make targets with workflow expectations instead of creating parallel meanings
- surface failures at the target that owns them

## First Proof Check

- `makes/bijux-py/ci/`
- workflow files that call the targets

