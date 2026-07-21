---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Extensibility Model

Extend Lab when a capability changes how scientifically motivated work is designed, checked, scheduled, handed off, observed, or reconciled. An extension must strengthen the closed operational loop rather than add another recommendation channel or integration shortcut.

## Supported extension shapes

### Assay and experimental design

New assay planning belongs in `planning/assays.py`; reusable layout and control logic belongs in `design`. Define required inputs, acceptance criteria, replicates, contrasts, randomization or multiplex constraints, material consumption, QC placement, and foreseeable failure modes. Advisory and executable forms must remain distinguishable.

### Readiness and scheduling policy

Add a readiness signal under `readiness` when it can independently block or qualify execution. Add capacity, queue, or scenario logic under `planning`. Scheduling must account for family capacity, instrument availability, material feasibility, staffing, and review pressure without changing the scientific priority silently.

### Handoff destination or artifact

Add domain-specific packets, risks, and transition review under `handoffs`. A new destination requires explicit field mappings, information-loss reporting, protocol and control attachments, canonical serialization, and structured refusal behavior. Destination convenience cannot erase an unsupported field or caveat.

### Outcome and reconciliation

New observation types belong in `outcomes`; planned-versus-observed interpretation belongs in `reconciliation`. Specify QC state, failure classification, acceptance operators, reliability, rerun policy, and evidence-promotion conditions. Reconciliation may propose operator actions or Intelligence feedback, but it must retain both the original plan and the observation.

### Operational benchmark

Use `benchmarks` for reproducible claims about the full lab loop: operator delivery, controlled failures, external review, follow-up burden, learning, and observed consequence. A benchmark is not a static success vignette; it must expose minimum controls, unsupported claims, and cases where a justified assay was low yield or an underestimated assay was useful.

## Admission criteria

Every extension must provide:

- a named owner within design, planning, readiness, lifecycle, handoff, outcome, reconciliation, or benchmark responsibility;
- typed advisory, blocked, executable, observed, failed, and unresolved states as applicable;
- explicit controls, protocol version, materials, staffing, capacity, and review dependencies;
- deterministic ordering and serialization for any delivered artifact;
- provenance links across plan, handoff, observation, and feedback;
- declared field loss at external formats such as LIMS exports;
- refusal behavior for missing authority, evidence, controls, or operational prerequisites;
- tests for nominal execution, blocked progression, partial observations, failures, reruns, and round-trip integrity;
- a root API ledger change only for a durable package-level entry point.

## Rejection rules

Do not place discovery algorithms, scientific-reference curation, advisory ranking policy, instrument drivers, credentials, or service orchestration in Lab. Do not label an assay executable while required controls or resources are unknown. Do not promote an outcome solely because a run completed, or hide a failed mapping behind a best-effort export.

An extension is complete when an operator can explain why the work was selected, whether it is ready, exactly what crosses the handoff, what happened, how reliable the observation is, and how that result changes—or does not change—the next cycle.
