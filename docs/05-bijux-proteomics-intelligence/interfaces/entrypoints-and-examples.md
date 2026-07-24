---
title: Entrypoints and Worked Examples
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Entrypoints and worked examples

The package root exposes owner modules, not a single orchestration function.
Import the smallest owner that matches the decision being made. There is no
standalone intelligence CLI or HTTP API; runtime integration belongs to the
runtime package.

## Rank a candidate set

```python
from bijux_proteomics_intelligence.candidates import (
    RankedCandidate,
    RankingWeights,
    rank_candidates,
)

candidates = [
    RankedCandidate(
        candidate_id="kinase-a",
        sequence="MPEPTIDEK",
        metrics={"mean_plddt": 87.0, "novelty": 0.35},
        provenance={"source": "structure-screen-2026-07"},
    ),
    RankedCandidate(
        candidate_id="kinase-b",
        sequence="MPEPTIDER",
        metrics={"mean_plddt": 79.0, "novelty": 0.72},
        provenance={"source": "structure-screen-2026-07"},
    ),
]

scores = rank_candidates(
    candidates,
    weights=RankingWeights(confidence=0.4, stability=0.35, novelty=0.25),
)
for score in scores:
    print(score.rank, score.candidate_id, score.score, score.reasons)
```

The ranking is a review input. Use `select_candidates()` when the workflow also
needs a Pareto front, frozen shortlist, and explicit `human_required` marker.

## Generate a falsification route

```python
from bijux_proteomics_intelligence.falsifiers import generate_falsifiers

# `claim` is an EvidenceClaim from bijux-proteomics-knowledge.
report = generate_falsifiers(claim)
for entry in report.entries:
    print(entry.claim_id, entry.falsifier_type, entry.required_evidence)
```

Falsifiers are most useful before a review decision. They state what result
would overturn the claim and prevent supporting evidence from becoming the only
visible path.

## Apply strong-claim refusal

```python
from bijux_proteomics_intelligence.refusal import (
    ClaimRefusalThresholds,
    refuse_unsupported_claims,
)

refusal = refuse_unsupported_claims(
    claims,
    thresholds=ClaimRefusalThresholds(
        minimum_strong_claim_confidence=0.8,
        minimum_peptide_support_count=2,
        require_valid_design=True,
        block_failed_qc=True,
    ),
)
for entry in refusal.entries:
    if entry.refused:
        print(entry.claim_id, entry.refusal_reason, entry.minimum_missing_evidence)
```

The refusal surface intentionally returns a report rather than raising. A claim
can remain in the evidence memory while being blocked from a stronger decision.

## Choose an owner

- `candidates` owns validation, ranking, Pareto selection, lifecycle, and store
  behavior.
- `claims`, `contradictions`, and `falsifiers` own challengeable claim posture.
- `judgment` owns policies, scenarios, paths, recommendations, and benchmarks.
- `posture` owns evidence readiness and skeptical review.
- `reviews` owns board, outsider, rerun, scrutiny, and release packets.
- `next_steps` translates explicit weaknesses into follow-up experiments.
- `learning` records adaptation without erasing prior decisions.

Persist the policy-bearing result and its evidence references before rendering
a narrative summary.
