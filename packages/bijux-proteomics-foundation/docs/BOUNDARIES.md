# Boundaries

## Package identity

- Distribution name: `bijux-proteomics-foundation`
- Import root: `bijux_proteomics_foundation`

## This package owns

- schema profile models
- canonical JSON, hashing, and fingerprint helpers under `serialization`
- shared identifiers under `identity`
- shared provenance and support-state contracts under `support`
- shared refusal and operation-result contracts under `outcomes`
- migration and compatibility utility behavior

## This package does not own

- program lifecycle and gate logic
- candidate ranking and decision policies
- evidence conflict semantics or lab planning behavior

## Dependency direction

This package may be imported by every other publishable package in the
repository because it owns the low-volatility document primitives those
packages share.

It should not grow runtime adapters, orchestration logic, or policy semantics
from higher layers.

## Downstream expectations

Downstream packages should rely on this package for schema identity,
serialization determinism, and migration helpers instead of rebuilding those
rules locally.

## Escalation signals

- if a shared identifier, schema, serialization, or migration primitive would
  otherwise be copied into multiple higher-layer packages, escalate it here
- if a proposed foundation helper needs lifecycle, evidence, ranking, lab, or
  runtime meaning to make sense, escalate it back to the owning package instead
- if a low-level primitive starts growing operator-facing payload rules or
  orchestration concerns, treat that as a boundary failure and redesign the seam

## Review questions

- does the change define a shared document primitive rather than a higher-layer
  policy or execution concern
- would keeping it out of foundation force multiple packages to invent
  divergent schema, serialization, identifier, or migration behavior
- can the change still be justified without claiming lifecycle, evidence,
  ranking, lab, or runtime ownership here
