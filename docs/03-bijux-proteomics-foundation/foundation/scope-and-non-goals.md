---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Scope and Non-Goals

`bijux-proteomics-foundation` exists for shared payload meaning. It should stay narrow enough that a
reviewer can tell what it is not for before reading implementation detail.

## In Scope

- work that directly strengthens the package's named role
- contracts, helpers, and tests whose best proof lives in this package
- explicit handoff points to neighboring packages

## Out Of Scope

- behavior whose best proof already lives in a neighboring package
- convenience abstractions that blur ownership
- repository-health automation or root process unless this is the maintainer
  package

## First Proof Check

- package source and tests
- neighboring handbooks when scope starts to blur
