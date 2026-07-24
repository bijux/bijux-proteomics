---
title: Compatibility Commitments
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Compatibility commitments

Intelligence compatibility preserves the interpretation and auditability of a
decision, not merely the ability to deserialize its final action. Consumers
must be able to distinguish changed evidence, changed policy, and changed
implementation across versions.

## Public surface

The `bijux_proteomics_intelligence` root lazily exposes owner modules for belief
audits, candidates, claims, contradictions, falsifiers, governance,
interpretation, judgment, learning, next steps, posture, query, refusal, and
reviews. Stable functions and models live in those domain modules; the root
does not flatten every symbol into one namespace.

| Contract | Compatibility promise |
| --- | --- |
| candidate results | identity, exclusions, factor reasons, scores, and policy lineage remain interpretable |
| scenario and counterfactual results | assumptions and perturbations remain explicit |
| refusal records | reason codes and remediation retain their declared meaning |
| review artifacts | evidence, policy, uncertainty, and human authority remain recoverable |
| learning records | prior advice is preserved and later outcomes append new evidence |
| `proteomics-intelligence` | forwards the canonical surface without independent policy |

## Semantic change triggers

A default weight, factor direction, threshold, tie breaker, confidence mapping,
refusal condition, downgrade order, or scenario aggregation rule can change an
outcome without changing a schema. Treat those edits as public semantic changes.
Record the policy identity and compare known decision cases before and after.

Adding an optional diagnostic is normally additive when old consumers can
ignore it safely. Removing an explanation field, changing a reason code, or
turning a refusal into a recommendation is breaking for audit consumers even
if the final model still validates.

## Determinism and evolution

Given the same versioned evidence, policy, and configuration, deterministic
surfaces return the same ordering and decision records. Where ties or numerical
tolerances exist, their resolution is part of the policy contract. Learning
does not mutate an earlier decision; it creates a new linked record so the old
information state remains reviewable.

## Verification

```bash
make test PACKAGE=bijux-proteomics-intelligence
make api PACKAGE=bijux-proteomics-intelligence
make build PACKAGE=bijux-proteomics-intelligence
make test PACKAGE=proteomics-intelligence
```

Compatibility evidence includes frozen policy fixtures, threshold and tie
boundaries, disagreement and refusal cases, serialized review packets, and the
forwarding alias when exported modules change. Release notes state whether the
change affects ranking, explanation, uncertainty, refusal, or packaging only.

No compatibility promise grants Intelligence execution or laboratory
authority. An old consumer that treated advisory output as an instruction was
already outside the supported contract.
