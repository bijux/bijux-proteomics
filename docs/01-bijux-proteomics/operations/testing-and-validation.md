---
title: Testing and Validation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Testing and Validation

Validation in `bijux-proteomics` is layered. Packages prove their own behavior.
The repository proves seams between packages, tracked contracts, docs, and
release orchestration.

## Change Class To Proof Surface

- package-local behavior: package unit, integration, and invariant tests
- API or schema changes: tracked artifacts under `apis/` plus freeze or drift
  checks
- docs and metadata changes: docs integrity checks and repository validation
- release-path changes: workflow, metadata, and publication guard checks
- runtime migration changes: the dedicated runtime migration validation suite

## First Proof Check

- package test suites under `packages/*/tests`
- tracked contract artifacts under `apis/*/v1`
- repository checks carried by `bijux-proteomics-dev` and workflow entrypoints

## Rule

A prose promise is unfinished until a package test, root check, or tracked
artifact can detect its drift.
