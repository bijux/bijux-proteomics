---
title: Decision Policy Configuration
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Decision policy configuration

Intelligence behavior is configured through typed, serializable policies—not
global settings or environment variables. The policy is part of the evidence
for a ranking or recommendation because changing weights, thresholds, metric
direction, or tie-breaking can change the decision while inputs remain fixed.

## Candidate ranking policy

`RankingPolicy` records:

- stable `policy_id`, `policy_family`, and monotonic `policy_version`;
- the minimum fraction and coverage of required metrics;
- minimum evidence support and optional manufacturability floor;
- weights for criteria, evidence, manufacturability, liability, and
  uncertainty;
- uncertainty penalty, diversity bonus, and ordered tie-break rules;
- a metric catalog defining class, unit, direction, and normalization.

```python
from bijux_proteomics_intelligence.judgment.policies import (
    MetricDefinition,
    MetricDirection,
    RankingPolicy,
    ScientificMetricClass,
    ranking_policy_lineage,
    validate_factor_weights,
)

policy = RankingPolicy(
    policy_id="candidate-review",
    policy_version=3,
    minimum_evidence_support=0.65,
    metric_catalog=[
        MetricDefinition(
            metric_key="binding_kd_nm",
            metric_class=ScientificMetricClass.AFFINITY,
            unit="nM",
            direction=MetricDirection.LOWER_IS_BETTER,
        )
    ],
)

weight_audit = validate_factor_weights(policy)
lineage = ranking_policy_lineage(policy)
```

Do not run a governed ranking when required metric definitions are missing,
factor weights are negative or unnormalized, or units and direction semantics
are ambiguous. Preserve the policy fingerprint with ranking provenance.

## Scenario and evidence gates

Progression, synthesis, scale-up, and redesign each have their own policy
models. Their thresholds govern evidence support, confidence, blocker burden,
residual risk, safety posture, and when a hold or redesign is required.
`evaluate_all_scenarios()` keeps their actions separate before computing
consensus.

Evidence readiness has independent configuration:
`assess_recommendation_readiness()` accepts minimum trust and record-count
thresholds, then also checks freshness, contradiction posture, evidence-kind
diversity, decisive support, and source diversity. Passing a ranking threshold
does not bypass this gate.

## Configuration invariants

- Candidate values and policy values are different inputs; never copy a score
  into a threshold to force a desired outcome.
- A policy version change requires new lineage even when the identifier stays
  stable.
- Missing evidence is not a zero-valued metric unless the metric contract says
  so explicitly.
- Scenario disagreement and confidence spread remain report fields, not
  settings to suppress.
- Promotion from advisory output to enforced policy is a recorded governance
  event, not a configuration default.
