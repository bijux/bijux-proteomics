# Package boundaries

## Package identity

- Distribution name: `proteomics-knowledge`
- Import root: `proteomics_knowledge`
- Canonical behavior owner: `bijux-proteomics-knowledge`

## This package owns

- the short Knowledge installation and import names
- forwarding for supported evidence, claim, grounding, and reconciliation surfaces
- compatibility evidence for `proteomics_knowledge` callers

## This package does not own

- independent evidence schemas, source resolution, contradiction, or sufficiency policy
- scientific computation, Runtime execution, recommendation policy, or lab planning
- alternate biological identity or provenance semantics

## Downstream expectations

Short-name consumers receive canonical Knowledge records and reconciliation
behavior. Evidence history and grounding rules remain owned by
`bijux-proteomics-knowledge`.

## Escalation signals

- route new evidence and grounding semantics to canonical Knowledge first
- stop when alias code rewrites provenance, context, support, or contradiction state
- escalate when a change could make historical evidence records resolve differently

## Review questions

- do both import paths preserve evidence identity and append-only history
- is every alias export backed by a canonical Knowledge public surface
- does the change avoid importing recommendation or laboratory policy into evidence custody
