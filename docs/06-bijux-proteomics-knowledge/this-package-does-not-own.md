---
title: This Package Does Not Own
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-05-09
---

# This Package Does Not Own

Package: `bijux-proteomics-knowledge`  
Import root: `bijux_proteomics_knowledge`

Knowledge owns cited evidence memory. It should not become a hidden execution,
recommendation, or lab-planning layer simply because many other packages read
its records.

## Supported Package-Root Imports

- `EvidenceBundle`
- `EvidenceClaim`
- `EvidenceRecord`
- `KnowledgeDecisionBrief`
- `evaluate_schema_compatibility`

## Allowed Package Dependencies

- `bijux-proteomics-core`
- `bijux-proteomics-foundation`

Knowledge may rely on shared primitives, but it should not import higher
product packages to explain evidence truth.

## Excluded Responsibilities

- execution orchestration and runtime replay behavior
- route-shaped payloads, transport-bound views, and operator endpoint shaping
- candidate ranking, recommendation, and selection policies
- laboratory scheduling and outcome rerun policies
- generic uncited context storage

## Route Elsewhere

- Use `bijux-proteomics-runtime` when the work changes replay, execution, or
  operator delivery surfaces.
- Use `bijux-proteomics-intelligence` when the work changes ranking posture,
  refusal logic, or analytical recommendation language.
- Use `bijux-proteomics-lab` when the work changes assay planning, readiness,
  or observed-outcome handling.
