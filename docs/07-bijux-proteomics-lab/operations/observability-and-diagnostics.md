---
title: Observability and Diagnostics
audience: lab-operator
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Observability and Diagnostics

Lab observability connects recommendation, plan, operational readiness,
execution handoff, observation, and outcome. These are durable scientific and
operational records. They explain more than a process log because they preserve
the reasons an assay was accepted, deferred, refused, or interpreted.

## Inspect the operational chain

| Boundary | Diagnostic signals |
| --- | --- |
| Recommendation intake | candidate and evidence identifiers, review posture, unresolved questions, requested follow-up |
| Assay planning | assay rationale, expected information gain, sample requirements, controls, review gates |
| Risk and feasibility | risk findings, predicted failure risk, missing controls, feasibility and readiness scores |
| Capacity and scheduling | feasible and deferred batches, instrument and staff availability, slot utilization, schedule pressure |
| Materials | required quantities, inventory sufficiency, reservation state, material-blocked candidates |
| Handoff validation | accepted and rejected assay identifiers, blockers, required next actions, execution refusal |
| LIMS export | source-to-destination field map, record count, readiness state, and explicit loss notes |
| Execution outcome | assay observations, QC feedback, batch assessment, failure triage, and follow-up directive |

Use candidate, plan, batch, assay, sample, and observation identifiers as the
join keys. Every scheduled assay should trace to a plan and recommendation;
every observation should trace to an assay; every follow-up should trace to an
outcome. An orphaned identifier is an integrity issue, even when its individual
record validates.

## Separate blockers from failures

A deferred batch caused by capacity or materials did not fail experimentally.
A responsible handoff refusal is a safety outcome, not a service outage. A LIMS
loss note identifies an interchange limitation. A completed assay with adverse
QC is an observed scientific or operational failure. Preserve these states so
throughput metrics cannot convert blocked or refused work into unsuccessful
execution—or hide it as success.

An incident record should include the upstream decision and evidence
references, plan and batch identifiers, lifecycle state, risk findings,
readiness and practicality, missing controls or resources, schedule pressure,
handoff blockers, export loss notes, observations, and outcome classification.

Diagnostics are complete when a reviewer can explain why work was or was not
scheduled, what was transferred to the execution system, what actually
happened, and which evidence authorizes the next action.
