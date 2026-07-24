---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Performance and Scaling

Intelligence cost grows with candidates, evidence links, policies, scenarios, counterfactuals, and report detail. Explainability is part of the result, so throughput measurements that omit rationale, refusal checks, or provenance are not measurements of the supported contract.

## Cost dimensions

| Analytical surface | Scale driver | Required output retained at scale |
| --- | --- | --- |
| candidate ranking | candidates × features | component scores, policy identity, ties, and rationale |
| evidence readiness | claims, evidence records, conflicts, and age checks | downgrade and refusal reasons |
| scenario judgment | candidates × scenarios × policies | scenario assumptions and recommendation deltas |
| sensitivity and counterfactuals | perturbations × complete evaluations | changed inputs, changed result, and stability conclusion |
| interpretation | proteins, sites, contrasts, pathways, or annotations | caveats, missingness, and scope |
| review assembly | findings, traces, questions, and artifacts | deterministic ordering and critical provenance |
| learning feedback | prior decisions × observed outcomes | original posture and explicit adjustment |

## Preserve reviewability

Do not optimize by retaining only a final score. A ranking without its component signals cannot be audited; a readiness decision without blockers cannot be repaired; a counterfactual without the changed assumption cannot be interpreted.

Use stable candidate identifiers and deterministic tie-breaking. Parallel evaluation is safe only when each candidate or scenario is independent under the same immutable evidence and policy snapshot. Merge results in a defined order and calculate any portfolio-wide or cross-candidate constraints after the complete set is available.

## Benchmark evidence

The package carries ranking, confidence, sensitivity, regret, blinded-challenge, decision-quality, counterfactual, policy, recommendation-packet, and review-scale fixtures. These surfaces test behavior and comparative pressure; they do not establish a production latency service-level objective.

Run the relevant evidence directly:

```bash
python -m pytest \
  packages/bijux-proteomics-intelligence/tests/candidates/test_ranking_benchmark_surface.py \
  packages/bijux-proteomics-intelligence/tests/judgment \
  packages/bijux-proteomics-intelligence/tests/reviews
```

Record candidate count, evidence-link count, policy and scenario counts, perturbation count, wall time, peak memory, and report size. Also record recommendation stability: a faster evaluator that silently changes ties, refusals, or uncertainty is a correctness regression.

## Scaling pattern

Runtime should fan out immutable evaluation units, enforce resource limits, and collect artifacts. Intelligence should remain a deterministic function of typed evidence, explicit policy, and scenario inputs. Cache only complete analytical results keyed by all meaning-bearing inputs—including policy, evidence, context, and package versions.

When reports become too large for direct review, produce layered artifacts: a bounded summary, candidate-level entries, and traceable detail. Do not truncate critical blockers or provenance. Scale presentation by navigation, not by deleting the evidence that justifies the decision.
