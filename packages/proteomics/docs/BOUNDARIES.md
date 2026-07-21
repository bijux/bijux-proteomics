# Package boundaries

## Package identity

- Distribution name: `proteomics`
- Import root: `proteomics`
- Canonical behavior owner: `bijux-proteomics-core`

## This package owns

- the short `proteomics` installation and import names
- forwarding from the short CLI and Python surfaces to canonical Core behavior
- compatibility tests and release guidance for those names

## This package does not own

- scientific models, parsing, inference, quantification, or workflow acceptance
- benchmark evidence, Runtime orchestration, evidence policy, or laboratory consequence
- independent defaults, errors, serialization, or command semantics

## Downstream expectations

Callers may use the short name where compatibility requires it. New scientific
work should target the canonical Core surface, and observable alias behavior
must remain equivalent to its declared owner.

## Escalation signals

- route any new scientific capability to `bijux-proteomics-core`
- stop when an alias export cannot be explained as direct forwarding
- escalate before removing or changing a name used by documented consumers

## Review questions

- is every public symbol traceable to a canonical Core owner
- do errors, defaults, results, and command behavior remain equivalent
- does the change provide a migration route for any affected caller
