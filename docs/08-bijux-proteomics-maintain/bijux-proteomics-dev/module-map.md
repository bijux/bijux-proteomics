---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Module Map

The maintainer package stays legible only when helper families remain separated by job.

## Module Families

- `docs/` for documentation integrity, consistency, design debt, and badge/link checks
- `api/` for contract freezing and OpenAPI drift checks
- `release/`, `security/`, and `quality/` for publication, audit, and architecture gates
- `tools/` and `trusted_process.py` for maintainer-oriented utility workflows

## First Proof Check

- `src/bijux_proteomics_dev/docs/`
- `src/bijux_proteomics_dev/api/`, `release/`, `security/`, and `quality/`

