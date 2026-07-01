---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-01
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

## Why This Package Feels More Scientific Now

- the package now makes biological context a public owner surface instead of an
  implied helper behind trust pages
- claim grounding, contradiction handling, and curated references now sit
  beside pathway, complex, kinase, disease, drug-target, and ortholog lookups
  in one coherent scientific memory layer
- readers can now see where the repository keeps evidence discipline without
  confusing that role with recommendation policy

## Concrete Knowledge Families

| owner surface | current substance | why it matters |
| --- | --- | --- |
| `memory` | evidence bundles, claims, normalization, integrity, and reconciliation state | the repository can preserve hesitation and conflict instead of flattening them |
| `references` | workflow grounding, literature audits, and curated scientific support routes | public workflow language can be challenged against explicit reading pressure |
| `pathways`, `complexes`, `kinases` | mechanistic and regulatory biological context | analytical claims can be tied to real systems biology instead of generic labels |
| `drugs`, `disease`, `features`, `coverage` | therapeutic, disease, feature, and evidence-coverage context | downstream recommendation and lab burden can see what is missing or clinically relevant |
| `identity`, `orthologs` | entity reconciliation and cross-species context | claims stay stable across datasets and biological mappings |
| `reviews` and `contracts` | package-owned review seams and compatibility expectations | downstream packages cannot quietly rewrite knowledge-state semantics |

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
- keep literature pressure, context gaps, and identity reconciliation visible
  after benchmark packets have already looked strong

## What Readers Commonly Underestimate

- this package is where public scientific memory lives after benchmark packets
  are assembled and before recommendations are phrased
- this package decides whether a sentence is grounded, contradicted, stale, or
  context-thin before intelligence gets to sound confident about it
- this package now carries concrete biology rather than just generic evidence
  bookkeeping

## What A Serious Reader Can Verify

- whether a workflow claim is grounded by explicit references or only by
  repository tone
- whether contradiction has been preserved as structured state or silently
  collapsed into one confidence score
- whether biological context is broad enough to support the current sentence in
  pathways, complexes, kinases, disease, drug targets, and ortholog space
- whether downstream packages are inheriting evidence state or improvising it
  locally

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

## Best Reader Route

- start here when the question is whether `bijux-proteomics` really owns
  scientific memory and context or only benchmark packets plus careful wording
- continue to [Workflow Claim Grounding](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-claim-grounding/)
  when the dispute is about exact sentence support
- continue to [Workflow Literature Audits](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-literature-audits/)
  when the dispute is about citation freshness, gap pressure, or scientific
  backdrop honesty

## First Proof Check

- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge`
- `packages/bijux-proteomics-knowledge/tests`
- grounding, contradiction, and biological-context artifacts once a claim
  narrows to one surface
- neighboring handbook branches once a change crosses the local role
