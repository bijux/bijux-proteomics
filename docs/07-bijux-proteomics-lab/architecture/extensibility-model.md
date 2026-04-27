---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Extensibility Model

A good extension point in `bijux-proteomics-lab` makes future change cheaper without obscuring who still owns the result. A bad one turns the package into a generic hook system.

## Extension Rules

- add new structure when it directly improves planning or outcome promotion clarity
- prefer intelligence for recommendation policy and foundation/core for shared meanings
- new extension points should keep lab loop reviewable by operators and maintainers

## First Proof Check

- the modules exposing extension points
- tests that prove extension behavior stays inside the package boundary
- neighboring handbooks if the extension changes a cross-package contract
