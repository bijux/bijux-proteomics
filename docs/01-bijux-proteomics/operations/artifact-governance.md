---
title: Artifact Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Artifact Governance

Repository artifacts do not all mean the same thing. Some are governed source,
some are tracked contract references, and some are generated run output. Review
gets weaker when those classes are treated as interchangeable.

## Artifact Classes

- governed source under `docs/`, `packages/`, and root config files
- tracked contract artifacts under `apis/`
- generated local or CI output under `artifacts/`

## Authority Rule

When source, docs, and generated output disagree, source plus the governing
contract check wins. Generated output is evidence of a run, not an independent
source of truth.

## First Proof Check

- the file class the artifact belongs to
- the helper, test, or workflow that validates that class
