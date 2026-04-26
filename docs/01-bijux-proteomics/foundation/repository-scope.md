---
title: Repository Scope
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Repository Scope

The root should stay narrow. It exists to hold shared docs structure,
repository-wide validation and release framing, tracked API artifacts, and other
assets that genuinely cross package boundaries. It should not become a backup
owner for product behavior.

## Root Scope

- handbook structure and cross-package routing under `docs/`
- tracked contract artifacts under `apis/`
- repository-wide command, workflow, and release coordination under
  `Makefile`, `makes/`, and `.github/workflows/`
- workspace metadata and root governance files when they affect several
  packages together

## Out Of Scope

- runtime execution behavior
- evidence, decision, or lab semantics
- package-local contracts that happen to be reused elsewhere

## Failure Mode To Reject

A root change that adds product behavior because it is easier to wire once at
the top is usually the wrong change. Shared convenience is not the same thing
as shared ownership.

## First Proof Check

- root files only when the rule truly spans several packages
- otherwise the owning package handbook, code, and tests
