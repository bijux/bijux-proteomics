---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Extensibility Model

A good extension point in `bijux-proteomics-knowledge` makes future change cheaper without obscuring who still owns the result. A bad one turns the package into a generic hook system.

## Extension Rules

- add concepts here only when they are canonical knowledge concepts rather than downstream policy
- prefer explicit review or resolution paths over hidden precedence rules
- new extension points should make contradiction handling easier to inspect

## First Proof Check

- the modules exposing extension points
- tests that prove extension behavior stays inside the package boundary
- neighboring handbooks if the extension changes a cross-package contract
