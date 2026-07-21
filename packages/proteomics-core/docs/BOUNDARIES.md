# Package boundaries

## Package identity

- Distribution name: `proteomics-core`
- Import root: `proteomics_core`
- Canonical behavior owner: `bijux-proteomics-core`

## This package owns

- the explicit short-name Core distribution and import path
- forwarding to the canonical scientific API and CLI contract
- compatibility evidence for consumers using `proteomics_core`

## This package does not own

- alternate scientific types, algorithms, validation, or evaluation logic
- Runtime state, Knowledge evidence, Intelligence decisions, or Lab readiness
- a separate release posture from the canonical Core package

## Downstream expectations

Code importing `proteomics_core` receives the canonical Core behavior through a
compatibility surface. Scientific documentation and extension work belong to
`bijux-proteomics-core`.

## Escalation signals

- move new scientific exports into the canonical Core package first
- stop when the alias needs package-local domain models or transformations
- escalate when a canonical removal would strand a supported short-name caller

## Review questions

- does the alias expose only supported canonical Core symbols
- would direct canonical imports produce the same contract and failures
- are package metadata and compatibility tests updated together
