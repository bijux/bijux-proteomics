---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Extensibility Model

A good extension point in `bijux-proteomics-foundation` makes future change cheaper without obscuring who still owns the result. A bad one turns the package into a generic hook system.

## Extension Rules

- add a shared type only when multiple packages need the same durable meaning
- prefer versioned migrations over ad hoc fallback parsing
- keep extensions small enough that every downstream package can still review the change

## First Proof Check

- the modules exposing extension points
- tests that prove extension behavior stays inside the package boundary
- neighboring handbooks if the extension changes a cross-package contract
