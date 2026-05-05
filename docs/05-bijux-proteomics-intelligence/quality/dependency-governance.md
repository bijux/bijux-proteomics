---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency governance is really boundary governance under another name.

For `bijux-proteomics-intelligence`, dependency review should keep evidence, contracts, and lab execution explicit instead of letting the package collapse into a hidden application layer.

## Governance Model

```mermaid
flowchart TB
    change["new or changed dependency"]
    purpose{"improves evaluation or explanation work?"}
    boundary{"knowledge, contracts, and lab seams stay explicit?"}
    copying{"dependency avoids copied neighbor semantics?"}
    accept["dependency is governable"]

    change --> purpose
    purpose -->|yes| boundary
    purpose -->|no| reject1["reject or relocate"]
    boundary -->|yes| copying
    boundary -->|no| reject2["reject or isolate"]
    copying -->|yes| accept
    copying -->|no| reject3["redesign the integration"]
```

This page should make it obvious that a recommendation package gets weaker when it starts owning evidence semantics or execution behavior through dependency shortcuts.

## Review Rules

- guard the seams to evidence, contracts, and lab execution carefully
- avoid dependencies that turn the package into a hidden application layer
- prefer explicit inputs from neighbors over copied semantics

## First Proof Check

- `packages/bijux-proteomics-intelligence/tests`
- `src/bijux_proteomics_intelligence/candidates/`, `judgment/`, and `posture/`
- `src/bijux_proteomics_intelligence/reviews/`, `interpretation/`, and `learning/`

## Design Pressure

The easy mistake is to accept a useful dependency that lets intelligence behave like the application shell instead of a bounded decision layer.
