---
title: Security Gates
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Security Gates

Security gates here protect repository policy boundaries, not product-specific threat models.

## Gate Rules

- dependency allowlists and audit checks should stay reviewable in code
- security failures should point to the owning helper and policy surface
- do not hide repository risk behind passing product-package tests

## First Proof Check

- `src/bijux_proteomics_dev/security/dependency_allowlist.py`
- `src/bijux_proteomics_dev/security/pip_audit_gate.py`

