---
title: Python API Surface
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Python API surface

`bijux-proteomics-intelligence` is a Python decision-support library. It has no
standalone network API and no primary CLI contract. Runtime or an application
layer may expose intelligence results through a service, but that layer owns
transport, authentication, request validation, and process behavior.

## Package-root owner modules

```python
from bijux_proteomics_intelligence import (
    belief_audit,
    candidates,
    claims,
    contradictions,
    falsifiers,
    governance,
    interpretation,
    judgment,
    learning,
    next_steps,
    posture,
    query,
    refusal,
    reviews,
)
```

The root returns modules, not re-exported domain classes or functions. Modules
load lazily and unknown root names raise `AttributeError`. The machine-readable
root API budget is 14 symbols, matching these owner surfaces.

## Capability map

| Owner | Representative public operations and records |
| --- | --- |
| `candidates` | `Candidate`, `RankedCandidate`, `RankingWeights`, `rank_candidates`, `pareto_frontier`, `select_candidates`, `CandidateStore` |
| `claims` | `validate_claim_support`, support statuses, validation entries and reports |
| `contradictions` | claim-pair conflict classification and contradiction reports |
| `falsifiers` | claim-specific falsifier generation and required-evidence records |
| `refusal` | governed thresholds and explicit refusal of unsupported strong claims |
| `interpretation` | run, quantitative, pathway, PTM, contaminant, and contrast interpretations |
| `judgment` | ranking policies, scenarios, recommendations, uncertainty, escalation, and portfolio decisions |
| `reviews` | report contracts, benchmark review, decision briefs, rerun kits, and public-scrutiny packets |
| `belief_audit`, `query` | belief challenge and answerable result questions |
| `learning`, `next_steps` | outcome-driven adaptation and discriminating follow-up recommendations |
| `governance`, `posture` | charter and skeptical evidence posture |

## Import and call pattern

```python
from bijux_proteomics_intelligence import candidates

candidate_records = [
    candidates.RankedCandidate(
        candidate_id="candidate-alpha",
        sequence="MPEPTIDEK",
        metrics={"mean_plddt": 91.0, "novelty": 0.7},
    ),
    candidates.RankedCandidate(
        candidate_id="candidate-beta",
        sequence="MSEQUENCEK",
        metrics={"mean_plddt": 82.0, "novelty": 0.9},
    ),
]
selection = candidates.select_candidates(candidate_records, top_n=1)

assert selection.human_required is True
for score in selection.scores:
    print(score.candidate_id, score.rank, score.score, score.reasons)
```

Candidate selection records the ordered score components, Pareto frontier, and
frozen IDs while retaining `human_required=True`. A caller must not treat
`frozen_ids` as approval to progress a candidate.

Claim review follows the same owner pattern:

```python
from bijux_proteomics_intelligence.claims import validate_claim_support
from bijux_proteomics_intelligence.refusal import refuse_unsupported_claims
```

Support validation checks graph nodes and support edges. Refusal applies
governed minimums for design validity, QC, peptide support, and PTM
localization. These are distinct operations: a claim can be linked to evidence
and still fail a strength threshold.

## Output guarantees

Decision-facing reports use typed contracts and retain stable summaries,
reason codes, evidence references, policy details, and notes describing the
calculation boundary. TSV renderers are available for review tables where
applicable. Report validation detects incomplete claim support or missing
review fields rather than silently filling them.

## Failure and uncertainty

- Model validation rejects malformed policy and report payloads.
- Query operations return explicit not-found or unsupported states where the
  question cannot be answered from supplied results.
- Refusal outputs identify minimum missing evidence instead of returning a
  weakened affirmative claim.
- Scenario disagreement and confidence spread remain visible in decision
  support rather than being collapsed into one score.
- Missing evidence, a failed QC state, and a software error are different
  outcomes and must remain different to consumers.

Network consumers should serialize these contracts without inventing stronger
service-level meanings. See [Compatibility commitments](compatibility-commitments.md)
before changing reason codes, policy fields, or report schemas.
