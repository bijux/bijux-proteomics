# Boundaries

## Package identity

- Distribution name: `bijux-proteomics-foundation`
- Import root: `bijux_proteomics_foundation`

## This package owns

- schema profile models
- canonical JSON and fingerprint helpers
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
