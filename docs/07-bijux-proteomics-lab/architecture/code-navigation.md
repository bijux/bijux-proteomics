---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Code Navigation

`bijux-proteomics-lab` owns the operational reasoning that turns a scientifically justified follow-up into controlled, capacity-aware work—and turns observed results back into reviewable evidence. Its modules follow the lifecycle of an assay rather than a generic services layout.

## Public Boundary

The package root exposes three planning entry points: batch planning, an advisory assay plan, and an executable assay plan. `public_api.py` records their owners and release rationale. The larger set of typed reports and policies remains under explicit domain namespaces so callers do not mistake an internal planning component for a universal package contract.

`governance/charter.py` defines the five owned capabilities: assay planning, queueing, progression, handoff packets, and observed-outcome reconciliation. Use that boundary when a feature could plausibly belong to Intelligence, Core, or Runtime.

## Question-to-owner map

| Question | Owning module family | Principal outputs |
| --- | --- | --- |
| Is the experimental layout defensible? | `design` | design validation, contrasts, replication summaries, randomization, multiplexing, fractionation, QC insertion, carryover and sample-tracking advisories |
| What assay work is scientifically and materially possible? | `planning/assays.py` | advisory and executable plans, batch outlines, material constraints, review packets, and plan validation |
| Which work should happen next? | `planning/priorities.py`, `planning/next_cycle.py` | information gain, gate impact, burden, practicality, material reservations, cycle briefs, and next-cycle packets |
| When can the work run? | `planning/queue.py`, `planning/scheduling.py` | queue alignment, capacity advisories, scheduled batches, scenario comparisons, and pressure reports |
| Are controls, evidence, provenance, staffing, and reagents ready? | `readiness` | operational and stage-readiness reports with typed blocking signals |
| May the assay advance? | `lifecycle` | governed queue, promotion, and assay-stage transitions with history audits |
| What crosses into external execution? | `handoffs` | protocol attachments, risks, refusals, transition reviews, canonical envelopes, LIMS mappings, and QC feedback |
| What was actually observed? | `outcomes` | acceptance, QC state, failures, rerun policy, reliability, promotion readiness, and feedback records |
| How does observed behavior change follow-up? | `reconciliation` | planned-versus-observed deltas, operator actions, Intelligence feedback, and next-cycle work |
| Does a flagship claim survive operational rehearsal? | `benchmarks` | claim support, burden, minimum controls, failure rehearsals, learning artifacts, and outcome dossiers |

## Trace an assay round trip

Begin in `planning/assays.py` with the advisory or executable plan. Follow experimental-layout questions into `design/experiments.py`, protocol controls into `design/protocols.py`, and resource constraints into `readiness/operations.py` and `planning/scheduling.py`. A plan can be scientifically desirable and still be blocked by missing controls, unavailable material, staffing, capacity, or review backlog.

Before delivery, inspect `handoffs/risk.py` and `handoffs/explanations.py`. The latter can produce a structured refusal when the request exceeds the package's authority or lacks responsible execution conditions. `handoffs/serialization.py` protects artifact identity; `handoffs/exports.py` makes LIMS field mapping and information loss explicit.

After execution, enter through `outcomes/observations.py`, not the planner. Acceptance, failure triage, rerun decisions, reliability, and evidence-promotion readiness are derived from observed results. `reconciliation/follow_up.py` then compares planned and observed behavior and emits operator and Intelligence-facing feedback without rewriting the original plan or observation.
