---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-04
---

# Data Contracts

Data contracts in `bijux-proteomics-knowledge` include schemas, structured models, and any stable
payload shape that neighboring systems are expected to understand.

This page keeps data shape changes reviewable. If a record or payload matters to
another package, another process, or a replay path, it deserves to be described
as a contract rather than left implicit in implementation details.

## Visual Summary

```mermaid
flowchart RL
    schema["schema.py: compatibility reports and schema profile"]
    serialization["serialization.py: canonical json + fingerprints"]
    evidence["evidence.py: evidence bundle and record shapes"]
    claims["claims.py: claim and lineage shapes"]
    resolution["resolution.py: conflict resolution shapes"]
    schema --> serialization
    evidence --> claims --> resolution
    schema --> evidence
```

## Contract Anchors

- `src/bijux_proteomics_knowledge/schema.py`
- `src/bijux_proteomics_knowledge/serialization.py`
- `src/bijux_proteomics_knowledge/evidence.py`
- `src/bijux_proteomics_knowledge/claims.py`
- `src/bijux_proteomics_knowledge/resolution.py`

## Artifact Anchors

- evidence bundles
- decision lineage views
- conflict-resolution summaries

## Concrete Anchors

- `src/bijux_proteomics_knowledge/schema.py`
- `src/bijux_proteomics_knowledge/serialization.py`
- `packages/bijux-proteomics-knowledge/tests/test_schema.py`
- `packages/bijux-proteomics-knowledge/tests/test_serialization.py`

## Use This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Data Contracts` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What This Page Answers

- which public or operator-facing surfaces `bijux-proteomics-knowledge` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Reviewer Lens

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Honesty Boundary

This page can identify the intended public surfaces of `bijux-proteomics-knowledge`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Next Checks

- move to operations when the caller-facing question becomes procedural or environmental
- move to quality when compatibility or evidence of protection becomes the real issue
- move back to architecture when a public-surface question reveals a deeper structural drift

## Purpose

This page explains which structured shapes deserve compatibility review.

## Stability

Keep it aligned with tracked schemas, stable models, and durable artifacts.
