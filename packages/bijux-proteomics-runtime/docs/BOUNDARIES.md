# Boundaries

This boundary contract is mandatory for runtime migration and follow-on work.

## Allowed dependencies

`bijux-proteomics-runtime` may depend on:

- `bijux-proteomics-foundation`
- `bijux-proteomics-core`
- `bijux-proteomics-knowledge`
- `bijux-proteomics-intelligence`
- `bijux-proteomics-lab`

## Runtime ownership

This package owns:

- interfaces (CLI and HTTP API)
- execution control and orchestration coordination
- provider binding and provider invocation
- runtime state transitions
- workspace state and run artifacts
- replay and determinism enforcement

## Runtime non-ownership

This package does not own:

- canonical domain definitions
- evidence semantics and contradiction semantics
- scoring policy semantics and recommendation semantics
- lab planning semantics and experiment promotion semantics

## Dependency direction law

Lower layers must not import runtime modules.

Specifically, the following package families must not import
`bijux_proteomics_runtime`:

- `bijux_proteomics_foundation*`
- `bijux_proteomics*` (core)
- `bijux_proteomics_knowledge*`
- `bijux_proteomics_intelligence*`
- `bijux_proteomics_lab*`

Runtime adapts lower layers. Lower layers remain runtime-agnostic.
