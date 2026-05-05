---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency governance is really boundary governance under another name.

For `bijux-proteomics-foundation`, a dependency change is acceptable only when it strengthens shared contract work without smuggling in package-specific policy or hidden operational ownership.

## Governance Model

```mermaid
flowchart TB
    change["new or changed dependency"]
    purpose{"serves shared contract purpose?"}
    boundary{"keeps package-specific policy out?"}
    proof{"versioning and adapter posture stay explicit?"}
    accept["dependency is governable"]

    change --> purpose
    purpose -->|yes| boundary
    purpose -->|no| reject1["reject or relocate"]
    boundary -->|yes| proof
    boundary -->|no| reject2["reject or relocate"]
    proof -->|yes| accept
    proof -->|no| reject3["pin, isolate, or redesign"]
```

This page should help a reviewer judge whether a dependency still belongs in a shared-contract package. If the dependency starts carrying local behavior, the package seam has already weakened.

## Review Rules

- keep dependencies minimal and shared-purpose
- do not add package-specific policy dependencies to foundation
- prefer versioned adapters over hidden dependency magic

## First Proof Check

- `packages/bijux-proteomics-foundation/tests`
- `src/bijux_proteomics_foundation/documents.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization/`

## Design Pressure

The easy failure is to accept a convenient helper dependency that quietly turns foundation into the hidden owner of policy or operational behavior.
