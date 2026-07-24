---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Domain Language

Decision language must reveal policy and uncertainty rather than make a score sound like authority.

| Term | Meaning |
| --- | --- |
| **candidate** | A bounded entity being evaluated, with identity, evidence references, metrics, flags, provenance, and confidence |
| **candidate cohort** | The exact comparison set to which a ranking applies |
| **fingerprint** | Stable identity for the contract-relevant candidate state used in an evaluation |
| **evidence posture** | A structured account of support, gaps, contradictions, provenance, and readiness |
| **falsifier** | An observation or test that would weaken or overturn a favored interpretation |
| **scenario** | A declared decision context with assumptions, actions, confidence, and unresolved questions |
| **policy** | Explicit gates, criteria, thresholds, weights, and uncertainty treatment used to reach an outcome |
| **score** | A policy-dependent numerical evaluation; not an intrinsic property of a candidate |
| **ranking** | An ordering valid for one cohort, evidence snapshot, and policy |
| **hold pressure** | The degree to which scenario evaluations favor delaying action |
| **confidence spread** | Variation in confidence across scenarios, used to expose instability |
| **downgrade chain** | Ordered reasons a stronger recommendation became conditional, held, or refused |
| **refusal** | A governed non-recommendation that names the unmet condition and minimum missing evidence |
| **escalation** | A requirement for human arbitration because conflict or uncertainty exceeds policy limits |
| **advisory output** | Decision support with no execution authority |
| **enforced policy** | An advisory output explicitly promoted by a named actor under a named policy |
| **regret** | Retrospective cost of a decision compared with an alternative after outcomes are known |

A high score is not high confidence, a top rank is not evidence truth, consensus is not certainty, and enforcement is not scientific validation. Each statement answers a different question and must retain its policy and evidence context.
