---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# CLI Surface

CLI documentation should describe the commands the package truly owns, not the commands a reader might wish existed.

## Package Surface

- there is no standalone CLI product owned directly by this package
- review and curation flows should be expressed through imports, payloads, or higher-level tooling
- avoid inventing command surfaces that imply this package also owns runtime operations

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py`, `memory/models/evidence.py`, and `memory/integrity/graph.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py`, `reviews/decision_briefs.py`, and `reviews/provenance.py`
- `packages/bijux-proteomics-knowledge/tests`
