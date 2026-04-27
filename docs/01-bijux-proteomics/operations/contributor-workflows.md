---
title: Contributor Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Contributor Workflows

Contributor flow should be repeatable enough that package ownership and proof
surfaces stay visible from the first edit to the final review. The most common
failure mode is not a bad command. It is starting in the wrong owning surface
and only discovering that after several files drift together.

## Common Workflow Shape

- start in the owning handbook before editing shared files
- make package-local changes in the owning package when behavior is local
- use root automation only when the work spans docs, schemas, release flow, or
  several packages
- update explanation and proof in the same change series

## First Proof Check

- the handbook page that justified the starting surface
- the owning package or root process files
- the tests or checks that prove the changed behavior
