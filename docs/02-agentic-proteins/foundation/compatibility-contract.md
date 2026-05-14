---
title: Compatibility Contract
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-05-09
---

# Compatibility Contract

`agentic-proteins` is not a second runtime and it is not a fallback place for
new product logic. Its durable role is narrower: preserve legacy entrypoints
while callers migrate toward the canonical runtime package.

## What This Package Owns

- compatibility forwarding for historical import roots
- legacy CLI and HTTP entrypoints that still need the old package name
- migration-safe routing toward canonical runtime, core, and intelligence
  owners

## What This Package Does Not Own

This package does not own canonical runtime behavior or new scientific owners.

- new canonical execution behavior
- new benchmark, evidence, recommendation, or lab source-of-truth logic
- repository-wide maintainer automation

## Public Import Rule

If a new import surface cannot be explained as compatibility forwarding, it
does not belong here. New integrations should target canonical packages
directly, especially `bijux-proteomics-runtime`.

## Release Rule

Release language must keep `bijux-proteomics-runtime` as the canonical
execution owner and `agentic-proteins` as the compatibility bridge. Any change
that makes the bridge feel equally authoritative is a release-blocking drift.

## Migration Proof

- `make quality-runtime-migration-validation`
- `docs/01-bijux-proteomics/operations/runtime-migration-validation.md`
- `packages/agentic-proteins/tests`

## First Proof Check

- `packages/agentic-proteins/src/agentic_proteins`
- `packages/agentic-proteins/README.md`
- `docs/02-agentic-proteins/interfaces/public-imports.md`
