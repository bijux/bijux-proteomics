---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Extensibility Model

A good extension point in `bijux-proteomics-intelligence` makes future change cheaper without obscuring who still owns the result. A bad one turns the package into a generic hook system.

## Extension Rules

- add metrics, evaluators, or loop controls only when they keep decision ownership explicit
- prefer knowledge for evidence semantics and lab for operational follow-through
- new extension points should improve reviewability of why a recommendation changed

## First Proof Check

- the modules exposing extension points
- tests that prove extension behavior stays inside the package boundary
- neighboring handbooks if the extension changes a cross-package contract
