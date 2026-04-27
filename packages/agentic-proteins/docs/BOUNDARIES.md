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

## Escalation signals

- if a change is needed only to preserve legacy imports or entrypoints during
  migration, escalate it here as a forwarding-only compat surface
- if a proposed compat module needs fresh runtime, domain, evidence, ranking,
  or lab behavior, escalate it back to the canonical owning package instead
- if a compat helper stops being a thin forwarder and starts carrying new logic,
  treat that as a boundary failure and redesign the migration seam

## Review questions

- does the change preserve legacy continuity for an already-canonical surface
  instead of inventing new product behavior
- would the true implementation still belong entirely in canonical packages if
  the compat layer disappeared after migration
- can the change still be described as forwarding-only without ambiguity about
  the real runtime or lower canonical owner
