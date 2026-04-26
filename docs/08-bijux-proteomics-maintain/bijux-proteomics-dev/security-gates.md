---
title: Security Gates
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Security Gates

Repository-facing security checks live in `bijux-proteomics-dev` so dependency
policy and vulnerability enforcement are visible and reusable instead of being
buried in workflow YAML.

The useful question is never “did security run somewhere.” The useful question
is which checked-in helper or test is carrying the repository’s security
expectation today.

## Current Security Surfaces

- `security/pip_audit_gate.py`
- `security/dependency_allowlist.py`
- tests and workflow steps that execute those gates

