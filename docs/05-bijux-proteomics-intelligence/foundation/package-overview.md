---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-06-30
---

# Package Overview

`bijux-proteomics-intelligence` exists to turn evidence and program constraints
into scores, scenarios, recommendations, and explanations. The package is
useful only when that role stays narrow enough that a reviewer can say why it
exists without naming several different owners at once.

The package is more concrete now than this overview used to imply. It owns
several distinct analytical families: candidate ranking, interpretation,
judgment, recommendation posture, benchmark review, and learning refinement.
Those families now expose real public surfaces instead of one vague
"decision" layer.

## Concrete Analytical Families

- `candidates` for ranking, shortlist pressure, and falsifier-aware selection
- `interpretation` for typed run summaries, differential abundance, PTM, and
  workflow-review reading
- `judgment` for review-board decision paths and recommendation shaping
- `posture` for evidence readiness, downgrade pressure, and refusal posture
- `reviews` for benchmark-backed analytical review packets
- `learning` for refinement loops that respond to observed follow-up and review
  outcomes

## Why This Package Exists Separately

- knowledge can own grounded evidence and contradiction state without also
  owning ranking or recommendation policy
- core can own scientific truth and workflow contracts without collapsing into
  product-facing review posture
- lab can own assay consequence without pretending it owns analytical ranking
  or review-board judgment

## What It Owns

- score and rank candidates
- evaluate scenarios and loops
- render explanations and reports for decisions
- publish bounded recommendation posture and review surfaces without claiming
  scientific truth

## What It Refuses

- evidence truth and contradiction state
- durable program contracts
- execution orchestration

## Strongest First Checks

- start in `candidates`, `judgment`, and `posture` when the question is why
  one recommendation survived and another was downgraded
- start in `interpretation` and `reviews` when the question is how a workflow
  result becomes a bounded analytical reading
- hand off to knowledge when the missing argument is grounding or
  contradiction, not recommendation logic

## First Proof Check

- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- `packages/bijux-proteomics-intelligence/tests`
- neighboring handbook branches once a change crosses the local role
