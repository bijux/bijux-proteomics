---
title: Extensibility Model
audience: developer
type: architecture
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Extensibility Model

Intelligence extends through explicit analytical policy and review contracts.
A new ranking factor, scenario, interpretation, or recommendation is acceptable
only when readers can inspect what evidence it uses, how it changes judgment,
which uncertainty it preserves, and when it refuses to decide.

## Extension routes

| Need | Extend | Required evidence |
| --- | --- | --- |
| New candidate property | `candidates/` | validation, provenance, lifecycle effect, and non-opaque ranking use |
| New ranking factor | `candidates/ranking.py` or candidate review policy | named factor, normalization, weight, contribution rows, tie behavior, sensitivity, and stability |
| New claim type | `claims/`, `falsifiers.py`, `contradictions.py`, and `refusal.py` | graph support rule, adverse-evidence rule, falsifier, refusal threshold, and belief audit |
| New analytical interpretation | `interpretation/` | typed upstream artifact, explicit limits, supporting IDs, cautions, and no new source curation |
| New decision scenario | `judgment/scenarios.py` | stable policy identifier, required metrics, action set, reasons, uncertainty, and escalation rule |
| New review artifact | `reviews/` | identifier alignment, provenance, alternatives, caveats, known exclusions, and validation |
| New learning behavior | `learning/` | attributable outcome, prospective effect, drift report, and immutable prior decision |

## Policy design

Policy must be data, not scattered conditionals. Give it a stable identifier,
typed thresholds and weights, deterministic ordering, and an explanation for
every factor. Emit the enforced policy with the result. Test boundary values,
ties, missing evidence, contradictory evidence, and changes to one factor at a
time.

A ranking extension is incomplete if it exposes only a total score. It must
produce factor-level contributions, rejection or eligibility reasons, and
robustness evidence. A scenario extension is incomplete if it cannot express
`hold`, `redesign`, or escalation alongside favorable actions.

## Analytical safeguards

Every strong claim needs graph-backed support, contradiction handling, a
falsifier, and a refusal boundary. High-confidence claims must remain in belief
audits rather than bypass them. Interpretation modules may project evidence
into decision context, but may not manufacture curated facts or downgrade an
upstream QC failure.

Benchmark new judgment against blinded cases, counterfactual changes,
sensitivity, known decision traps, and a simpler baseline. Compare not only
agreement but regret, confidence calibration, stability, refusals, and the
quality of the explanation.

## Extension smells

- a new “AI” or score abstraction with no owned decision semantics;
- free-text evidence not linked to governed identifiers;
- a factor whose scale or direction is implicit;
- confidence increased by missing evidence;
- adverse evidence removed during synthesis;
- recommendations that contain executable lab instructions; or
- adaptation that mutates historical policy or decision artifacts.

An extension is complete when policy lineage, reasoning, uncertainty,
refusals, benchmark behavior, review output, and downstream authority remain
inspectable as one decision path.
