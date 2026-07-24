---
title: Code Navigation
audience: developer
type: architecture
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Code Navigation

Bijux Proteomics Intelligence turns governed scientific evidence into
reviewable analytical judgment. Navigate the package as a reasoning chain:
candidate state, claim support, evidence posture, explicit policy evaluation,
recommendation, review, and learning.

## Reasoning map

| Question | Start here | Owned result |
| --- | --- | --- |
| What is being evaluated? | `candidates/schema.py` and `candidates/records.py` | candidate identity, evidence references, metrics, and state |
| Is the candidate valid and eligible? | `candidates/validation.py`, `quality.py`, `filters.py`, and `selection.py` | validation, QC posture, exclusions, and shortlist membership |
| Why is one candidate ranked above another? | `candidates/ranking.py`, `fingerprints.py`, and `lifecycle.py` | factor contributions, policy lineage, robustness, stability, drift, and movement |
| Is a claim actually supported? | `claims/support.py`, `contradictions.py`, and `refusal.py` | graph-backed support, conflicting evidence, and governed claim refusal |
| What could overturn the claim? | `falsifiers.py` and `belief_audit.py` | claim-specific falsifiers, evidence for and against, uncertainty, and next checks |
| What does the evidence mean in context? | `interpretation/` | bounded readings of quantitative, contrast, PTM, pathway, contaminant, structure, and run evidence |
| What action is favored under a stated policy? | `judgment/policies.py`, `scenarios.py`, `recommendations.py`, and `paths.py` | advance, hold, redesign, or scale-up analysis with reasons and alternatives |
| What should a reviewer receive? | `reviews/decision_briefs.py`, `report_contract.py`, `boards.py`, and `candidates.py` | aligned claim, ranking, contradiction, rationale, and follow-up artifacts |
| How is public scrutiny supported? | `reviews/benchmark_reviews/`, `external_review_kits.py`, `independent_reruns.py`, and `public_scrutiny.py` | benchmark-linked review packets, caveats, rerun routes, and known exclusions |
| How does observed outcome influence future posture? | `learning/adaptation.py` and `learning/refinement/` | prospective adaptation, convergence, and stagnation evidence |

## Fast reading route

Start with `governance/charter.py`. It defines thirteen analytical bands and the
five capabilities they serve: prioritization, contradiction handling, review
reasoning, interpretation discipline, and recommendation. Then inspect
`public_api.py` before importing from package root; the root surface is curated
and is not a substitute for owner-module APIs.

For one decision, trace identifiers in this order: candidate → evidence → claim
→ policy → scenario → recommendation → review disposition. Compare every score
with its factor rows and every claim with support, contradiction, refusal, and
belief-audit entries. A final recommendation without these joins is not the
complete intelligence result.

Benchmark modules under `judgment/` test decision behavior—blinded challenges,
counterfactuals, regret, sensitivity, policy comparison, and confidence—not
scientific parsing. Core owns the upstream scientific artifacts, while
knowledge owns curated evidence graphs and references.
