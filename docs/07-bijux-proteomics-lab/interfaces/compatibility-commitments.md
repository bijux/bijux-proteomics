---
title: Compatibility Commitments
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Compatibility commitments

Lab compatibility protects operational safety and auditability. A payload is
not compatible when it still parses but changes whether work is advisory,
authorized, blocked, executable, observed, or eligible for evidence promotion.

## Stable contracts

| Surface | Commitment |
| --- | --- |
| advisory assay plans | remain explicitly non-executable and preserve rationale and blockers |
| readiness and refusal | reason codes, prerequisites, remediation, and authority retain meaning |
| executable plans and handoffs | protocol, materials, controls, review, and authorization remain recoverable |
| outcomes | raw observations, units, QC, censoring, failure class, and deviations remain distinct |
| reconciliation | requested, expected, observed, and follow-up states are not collapsed |
| `proteomics-lab` | forwards canonical root exports without independent lab policy |

The curated `bijux_proteomics_lab` root exposes
`plan_experiment_batches`, `build_advisory_assay_plan`, and
`build_executable_assay_plan`. Detailed contracts remain in their owner modules
so the root stays a deliberate planning surface.

## Safety-critical change triggers

Treat a change as compatibility-sensitive when it alters:

- the transition from advisory to executable state;
- required review roles, readiness checks, or refusal reasons;
- scheduling dependencies, capacity assumptions, or reservation semantics;
- protocol, control, material, sample, or instrument fields in a handoff;
- outcome units, QC state, censoring, failure classification, or promotion
  eligibility;
- idempotency keys, payload digests, or acknowledgement behavior.

An optional descriptive field can be additive. A default that turns missing
authorization into approval, missing QC into pass, or missing observations into
expected values is breaking regardless of schema validity.

## Artifact evolution

Persisted plans and outcomes are immutable records of distinct information
states. A migration creates a new governed representation linked to the source;
it does not rewrite what was authorized or observed. Flat LIMS or operator views
retain identifiers that resolve to the canonical typed artifact when nested
rationale cannot be represented.

## Verification

```bash
make test PACKAGE=bijux-proteomics-lab
make api PACKAGE=bijux-proteomics-lab
make build PACKAGE=bijux-proteomics-lab
make test PACKAGE=proteomics-lab
```

Compatibility evidence includes advisory/executable separation, refusal
boundaries, dependency cycles, capacity failures, handoff idempotency, outcome
round trips, reconciliation lineage, and alias forwarding. Release notes name
the operational state affected and any required operator or integrator action.
