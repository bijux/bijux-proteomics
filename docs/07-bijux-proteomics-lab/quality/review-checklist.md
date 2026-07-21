---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Review Checklist

Review Lab changes as changes to a safety- and evidence-bearing lifecycle, not
as ordinary record plumbing. Approval requires both correct behavior and a
reconstructable operator-facing history.

## Ownership And State

- Name the lifecycle state or transition being changed.
- Confirm the change belongs to Lab rather than Foundation, Core, Knowledge,
  Intelligence, or Runtime.
- Ensure advice, executable intent, readiness, handoff, observation, triage,
  and promotion remain distinct states.
- Require explicit rejection for illegal or incomplete transitions.

## Scientific And Operational Safety

- Re-evaluate prerequisites, controls, replicates, capacity, materials,
  staffing, and protocol versions.
- Preserve units, detection limits, censoring, and technical versus biological
  failure classes.
- Check queue ordering for hidden score, cost, capacity, or fairness changes.
- Confirm a stale readiness snapshot cannot authorize new work.

## Record Integrity

- Retain actor, timestamp, rationale, source identifiers, prior state, and
  resulting state where the contract requires them.
- Round-trip plans, handoffs, observations, and follow-up records.
- Compare old serialized fixtures when schema or defaults move.
- Keep promotion rationale and rejected alternatives linked to the observation.
- Verify review outputs still match the canonical record.

## Boundary And Failure Cases

| Challenge | Expected behavior |
| --- | --- |
| missing prerequisite or control | affected transition refuses |
| capacity changes after approval | readiness is re-evaluated |
| duplicated or replayed handoff | idempotent handling or explicit conflict |
| partial observation | incomplete state remains visible |
| below-detection value | censoring metadata is retained |
| technical failure | not promoted as biological evidence |
| contradictory follow-up | both evidence and reconciliation remain reviewable |
| downstream service unavailable | durable record remains readable and uncorrupted |

## Verification Route

Run the focused tests for the changed domain under
`packages/bijux-proteomics-lab/tests`, then package serialization, public API,
dependency, and documentation checks implicated by the change. Inspect emitted
artifacts and diffs; a passing transition test alone does not prove record
quality or downstream evidence safety.
