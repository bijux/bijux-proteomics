---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-06-30
---

# Package Overview

`bijux-proteomics-knowledge` exists to keep claims, evidence, confidence, and
contradiction state explicit and reviewable. The package is useful only when
that role stays narrow enough that a reviewer can say why it exists without
naming several different owners at once.

The package is also broader now than this older overview suggested. It does
not only hold generic evidence records. It owns selective scientific memory,
grounding references, contradiction-aware reconciliation, and concrete
biological lookup surfaces that downstream packages use to keep claims honest.

## Concrete Knowledge Families

- `memory` for evidence bundles, claims, normalization, integrity, and
  reconciliation state
- `references` for workflow grounding, literature audits, and curated
  scientific support routes
- biological lookup owners such as `pathways`, `complexes`, `kinases`,
  `drugs`, `disease`, `features`, `identity`, `orthologs`, and `coverage`
- `reviews` and `contracts` for package-owned review seams and compatibility
  expectations

## Why This Package Exists Separately

- core can own scientific truth without also becoming a long-lived memory and
  grounding store
- intelligence can own ranking and recommendation posture without inventing
  evidence state locally
- lab can reason about follow-up burden without becoming the keeper of claim
  grounding, contradiction history, or external scientific references

## What It Owns

- track claims and evidence records
- model confidence and contradiction state
- provide repositories and review seams for knowledge state
- resolve grounded biological context that later recommendation and lab routes
  should not improvise independently

## What It Refuses

- scoring policy
- lab workflow ownership
- operator-facing runtime behavior

## Strongest First Checks

- start in `memory` when the question is whether a claim, contradiction, or
  evidence bundle is explicit enough to review
- start in `references` when the question is whether a workflow sentence is
  grounded in cited scientific support
- start in the biological lookup owners when the question is whether pathway,
  complex, kinase, disease, drug-target, or ortholog context is actually
  available and reviewable

## First Proof Check

- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge`
- `packages/bijux-proteomics-knowledge/tests`
- neighboring handbook branches once a change crosses the local role
