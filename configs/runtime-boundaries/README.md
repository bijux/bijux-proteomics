# Runtime Boundary Policy

This directory holds policy inputs for automated runtime boundary enforcement.

## Coverage

- lower-layer imports that should never point upward to runtime
- compatibility-package forwarding policy for `agentic-proteins`
- runtime class-name collisions with canonical lower-layer ownership packages

## Allowlist intent

Allowlists in this directory are migration controls.

They exist to make boundary drift explicit, reviewable, and removable over time.
