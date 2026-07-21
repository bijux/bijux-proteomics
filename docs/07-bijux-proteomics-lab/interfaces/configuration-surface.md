---
title: Planning and Promotion Policy
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Planning and promotion policy

Lab configuration is carried by typed plans, policies, profiles, and declared
resources. There is no hidden package-wide configuration file. This keeps the
difference between scientific priority, operational feasibility, and evidence
promotion visible in the artifacts that cross the laboratory boundary.

## Planning policy

`PlanningPolicy` weights why a pending assay is worth doing:

- uncertainty reduction;
- contradiction resolution;
- falsification value;
- impact on a blocking decision gate;
- orthogonal confirmation;
- execution burden for blocking and non-blocking assays.

The policy has a stable `policy_id`. Preserve it with information-gain scores
and the resulting priority queue. A higher candidate score alone does not
guarantee higher lab priority when material, capacity, assay constraints, or a
more discriminating experiment changes the expected value of work.

## Design and readiness inputs

Experiment design operations take explicit controls rather than process-wide
defaults: contrast definitions, replication expectations, randomization seed,
batch and fraction capacity, multiplex channel roles, QC insertion interval,
plate dimensions, carryover thresholds, and protocol attachments.

Operational readiness is a separate input surface. Declare available sample
kinds, materials, reagents, instruments, staff, controls, budget, capacity,
lineage, and review clearance. Supplying one class of resource must not clear a
different blocker.

## Outcome and promotion policy

`AssayAcceptanceRule` defines the metric, comparison operator, threshold, and
unit for one assay. `OutcomePromotionPolicy` controls base confidence for
passed and failed outcomes plus the uncertainty penalty. Batch promotion adds
quality, reliability, QC, and lineage requirements across a complete batch.

Promotion policy does not rewrite an observation. It determines whether the
observation is eligible to become an evidence record and reports blocked
assays separately.

## Artifact policy

`LabArtifactProfile` and `LabArtifactContractRegistry` define accepted schema
versions, producers, and artifact kinds for handoff. Canonical envelopes carry
the artifact payload, document schema, and fingerprint; verification detects
payload tampering but does not prove biological correctness.

## Configuration invariants

- Keep advisory, executable, request, instruction, outcome, and promoted
  evidence models distinct.
- Persist policy identifiers, design parameters, declared readiness facts, and
  artifact fingerprints with each handoff.
- Treat randomization seed and channel assignments as experimental provenance.
- A failed assay may produce valuable negative evidence; technical or
  reproducibility failure usually cannot support the same biological claim.
- Never clear a blocker by mutating a returned plan. Record the new readiness
  evidence and rebuild the governed handoff.
