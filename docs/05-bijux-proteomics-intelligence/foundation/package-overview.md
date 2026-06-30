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

## Why This Package Feels More Real Now

- the package now exposes challenge, confidence, regret, and bounded
  recommendation surfaces that outsiders can inspect directly
- recommendation posture is no longer hidden inside one summary judgment; it is
  broken into candidate pressure, scenario reading, review packets, and
  follow-up learning loops
- the analytical layer now has enough public shape that readers can tell where
  intelligence adds judgment and where it must still defer to truth owners

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

## What Readers Commonly Underestimate

- this package is not just a recommendation button; it owns the public record
  of where analytical confidence breaks
- this package names regret and overconfidence explicitly, which means public
  recommendation authority can now be challenged with its own artifacts
- this package is where benchmark evidence turns into bounded policy language,
  not where benchmark evidence becomes truth

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

## Best Reader Route

- start here when the question is whether `bijux-proteomics` has a real
  analytical layer or only careful prose around benchmark packets
- continue to [Workflow Recommendation Challenges](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/workflow-recommendation-challenges/)
  when you need to see how recommendations behaved under hidden evidence
- continue to [Workflow Recommendation Confidence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/workflow-recommendation-confidence/)
  when you need to see where current posture is still too easy to overstate

## First Proof Check

- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- `packages/bijux-proteomics-intelligence/tests`
- neighboring handbook branches once a change crosses the local role
