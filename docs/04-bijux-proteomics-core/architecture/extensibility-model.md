---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Extensibility Model

A good extension point in `bijux-proteomics-core` makes future change cheaper without obscuring who still owns the result. A bad one turns the package into a generic hook system.

## Extension Rules

- extend the package when the change adds or clarifies durable contract meaning
- prefer downstream policy packages for heuristics, ranking, or lab workflow decisions
- keep new adapters narrow so runtime dependence remains legible

## First Proof Check

- the modules exposing extension points
- tests that prove extension behavior stays inside the package boundary
- neighboring handbooks if the extension changes a cross-package contract
