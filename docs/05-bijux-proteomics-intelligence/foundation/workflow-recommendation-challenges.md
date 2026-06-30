---
title: Workflow Recommendation Challenges
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-01
---

# Workflow Recommendation Challenges

`bijux-proteomics-intelligence` owns recommendation posture, so it also owns
the surfaces that can embarrass that posture.

These challenge pages exist to stop elegant decision prose from sounding more
trustworthy than the hidden evidence it depends on. The repository now ships
blinded recommendation challenges for every flagship workflow family that
currently carries outsider-facing recommendation posture.

## What The Challenge Actually Does

The sequence is simple and deliberate:

1. freeze the recommendation posture while some companion or perturbation
   evidence is still hidden
2. reveal the withheld pressure packet
3. publish whether the original recommendation landed as a hit, a miss, an
   overconfidence event, or an underconfidence event

That is why this surface matters. It tests whether the intelligence layer stays
honest when the easy-looking view is no longer the full view.

## What Ships

- one blinded recommendation challenge per flagship family:
  `dda_blinded_recommendation_challenge.json`,
  `dia_blinded_recommendation_challenge.json`,
  `lfq_blinded_recommendation_challenge.json`,
  `ptm_blinded_recommendation_challenge.json`,
  `targeted_blinded_recommendation_challenge.json`
- one cross-family overconfidence audit at
  `artifacts/intelligence/benchmark-decisions/workflow_overconfidence_audit.json`
- one cross-family underconfidence audit at
  `artifacts/intelligence/benchmark-decisions/workflow_underconfidence_audit.json`

## Current Family Outcomes

- `dda`: `1` hit, `1` overconfidence, `0` misses
- `dia`: `1` hit, `1` overconfidence, `0` misses
- `lfq`: `1` hit, `1` overconfidence, `0` misses
- `ptm`: `1` hit, `1` overconfidence, `0` misses
- `targeted`: `1` hit, `1` overconfidence, `1` miss

## How To Read Those Outcomes

| workflow family | strongest current reading |
| --- | --- |
| `dda` | the family can survive one blinded hit, but cross-engine reveal pressure still shows that import-backed confidence can sound cleaner than the harder adjacent package earns |
| `dia` | the recommendation layer still leans too optimistically on library-conditioned evidence when the harder matrix-shift view is revealed |
| `lfq` | recommendation posture remains bounded because sparse-contrast and missingness pressure still create visible overconfidence debt |
| `ptm` | localization can look recommendation-ready before ambiguity-aware consequence pressure pulls the sentence back down |
| `targeted` | the family shows the sharpest practical failure because interference and carryover pressure can collapse an action that still looked viable from the cleaner brief |

The targeted miss matters most right now. The hidden interference and carryover
perturbation collapses the follow-up lane that still looks actionable when only
the cleaner decision brief is visible.

## What These Challenges Prove

- recommendation posture is no longer judged only by summary confidence prose
- the repository can show where hidden evidence creates measurable
  overconfidence debt
- recommendation errors are published as first-class review surfaces instead of
  being folded back into vague caution language

## What They Do Not Prove

- that the benchmark packet itself is scientifically complete
- that one blinded hit authorizes broader public wording
- that intelligence can widen past grounding, runtime, or lab consequence
  boundaries on its own

## Best Next Routes

- Open [Workflow Recommendation Confidence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/workflow-recommendation-confidence/)
  when the question becomes cross-family overconfidence, underconfidence, or
  regret rather than one blinded reveal.
- Open [What Changed The Recommendation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-changed-the-recommendation/)
  when you need to see how comparator removal, literature removal, or burden
  changes move the sentence.
- Open [Workflow Consequence Maps](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-consequence-maps/)
  when the question is whether the challenged recommendation still survives the
  downstream assay burden it would trigger.

## Why This Belongs Here

These surfaces are intelligence work rather than core or knowledge work.

The benchmark packages, literature surfaces, and contradiction dossiers still
own truth. This package owns what the recommendation layer does with those
surfaces when it must choose, stay bounded, or refuse.
