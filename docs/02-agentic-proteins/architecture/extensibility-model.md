---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Extensibility Model

A good extension point in `agentic-proteins` makes future change cheaper without obscuring who still owns the result. A bad one turns the package into a generic hook system.

## Extension Rules

- add extension points only when they help retire or forward a legacy surface cleanly
- prefer new capability in `bijux-proteomics-runtime` or lower canonical packages
- remove bridge-only structure once migration proof shows it is no longer needed

## First Proof Check

- the modules exposing extension points
- tests that prove extension behavior stays inside the package boundary
- neighboring handbooks if the extension changes a cross-package contract
