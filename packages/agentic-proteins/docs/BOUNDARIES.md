# Boundaries

## Package identity

- Distribution name: `agentic-proteins`
- Import root: `agentic_proteins`
- Canonical replacement package: `bijux-proteomics-runtime`

## This package owns

- compatibility routing and legacy entrypoint continuity
- forwarding-only import surfaces for canonical runtime and lower packages
- migration-safe preservation of historical CLI and package roots

## This package does not own

- core program and review-gate domain contracts
- candidate-ranking and scenario decision policy logic
- evidence trust and contradiction-resolution semantics
- lab planning and execution-outcome scheduling behavior

## Dependency direction

Compat modules may import canonical packages in order to forward legacy import
paths, but canonical packages must not depend on `agentic_proteins`.

## Downstream expectations

Downstream users may keep legacy imports temporarily, but maintainers should
review every new compat surface as a forwarding rule, not as a place to grow
new implementation.
