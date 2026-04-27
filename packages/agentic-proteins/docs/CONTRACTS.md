# Contracts

## Public package identity

- Distribution name: `agentic-proteins`
- Import root: `agentic_proteins`
- Legacy CLI command: `agentic-proteins`
- Canonical replacement package: `bijux-proteomics-runtime`

## Stable contracts

- forwarding keeps legacy imports available while canonical packages own behavior
- CLI and API compatibility surfaces mirror canonical runtime contracts
- compat documentation names the canonical package that now owns each surface

## Change requirements

Behavioral changes in canonical runtime execution must be reflected by tests and
artifact expectations before compat forwarding is widened or rewritten.

Compat-specific changes should update the forwarding and boundary tests that
guard strict compat mode.

## Explicit non-contracts

- This package is not the canonical runtime.
- This package is not a place for new domain logic.
- This package does not define a permanent deprecation policy by itself.
