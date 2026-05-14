---
title: Observability and Diagnostics
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Observability and Diagnostics

Diagnostics should reveal whether a failure belongs to this package or to a neighbor.

## Operating Rules

- diagnostics should focus on invalid shared shapes, migration paths, and serialization failures
- cross-package fixtures are more useful than runtime dashboards here
- logs should help identify which version contract failed and why

## First Proof Check

- `src/bijux_proteomics_foundation/serialization/document_schema.py` and `compatibility/schema_migrations.py`
- `src/bijux_proteomics_foundation/serialization/`
- `packages/bijux-proteomics-foundation/tests`
