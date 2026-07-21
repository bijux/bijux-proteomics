---
title: Observability and Diagnostics
audience: decision-reviewer
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Observability and Diagnostics

Intelligence is observable through the structure of its reasoning artifacts.
The primary diagnostic is not a service metric but a trace from evidence to
claim, candidate factors, scenario outcomes, recommendation, and review action.
Operational logs may locate an exception; they cannot establish that a decision
was justified.

## Read the decision trace

| Artifact | Inspect |
| --- | --- |
| Evidence posture | completeness, freshness, conflicts, confidence, and unresolved questions |
| Candidate ranking | policy identifier, factor definitions, weights, normalized contributions, and stable ordering |
| Scenario evaluation | action per scenario, confidence, reasons, and disagreement across scenarios |
| Claim review | evidence for, evidence against, contradictions, uncertainty, falsifiers, and next checks |
| Refusal report | claim, threshold that failed, evidence references, and permitted recovery action |
| Decision brief | recommendation, rationale, alternatives, limitations, and escalation state |
| Review-board report | agenda item, recorded disposition, rationale, and follow-up actions |
| Learning history | observed outcome and prospective posture change without alteration of prior decisions |

Start with identifiers. Candidate, claim, evidence, policy, scenario, and review
identifiers should join across artifacts. Missing or mismatched identifiers are
contract defects because they break the audit path. Then reconcile summary
counts: every claim should have a refusal assessment, high-confidence claims
must appear in the belief audit, and referenced evidence must exist in the
governed evidence graph.

## Explain movement

When a recommendation changes, compare evidence membership and freshness first,
then policy lineage, factor contributions, contradiction state, confidence
downgrades, and scenario action spread. Report the smallest causal difference.
“The score changed” is not a sufficient diagnosis.

Confidence must be read with its support and uncertainty. A high baseline value
can be downgraded by weak support, unresolved contradictions, or incomplete
resolution. Likewise, consensus across scenarios is meaningful only when the
same evidence and policy were evaluated; differing actions are evidence for
escalation, not noise to suppress.

An incident record should contain the decision and policy identifiers, input
fingerprints, package version, candidate ordering, factor audit, evidence
posture, scenario outcomes, claim refusals, and relevant review rationale.
Diagnostics are complete when an independent reviewer can reproduce the path
and name exactly which evidence, rule, or uncertainty produced the outcome.
