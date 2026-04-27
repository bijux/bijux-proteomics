# Boundaries

## Package identity

- Distribution name: `bijux-proteomics-lab`
- Import root: `bijux_proteomics_lab`

## This package owns

- assay planning and dependency-aware batching
- schedule and capacity-aware next-cycle recommendation logic
- outcome interpretation and rerun policy modeling
- repository contracts for plans, queues, and feedback records

## This package does not own

- domain program lifecycle and gate invariants
- ranking and scenario recommendation models
- evidence trust and contradiction-resolution policy ownership

## Dependency direction

This package may depend on foundation primitives, core lifecycle state,
knowledge evidence inputs, and intelligence recommendations when it plans or
interprets laboratory work.

It should not become the owner of lifecycle authority, ranking policy, or
evidence truth semantics.

## Downstream expectations

Downstream packages should use this package as the canonical home for
dependency-aware planning and outcome promotion behavior instead of scattering
schedule logic across runtime or domain helpers.
