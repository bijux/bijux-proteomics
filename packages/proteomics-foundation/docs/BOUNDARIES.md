# Package boundaries

## Package identity

- Distribution name: `proteomics-foundation`
- Import root: `proteomics_foundation`
- Canonical behavior owner: `bijux-proteomics-foundation`

## This package owns

- the short Foundation installation and import names
- forwarding for supported identifiers, serialization, outcomes, and compatibility primitives
- compatibility evidence for the `proteomics_foundation` surface

## This package does not own

- independent schemas, canonicalization rules, hashes, identifiers, or migrations
- proteomics workflow policy, execution behavior, evidence semantics, or assay planning
- heavier dependencies or product-specific logic absent from Foundation

## Downstream expectations

Consumers may use the short import without receiving a different document
contract. Canonical serialization, identity, and migration semantics remain
defined by `bijux-proteomics-foundation`.

## Escalation signals

- add shared primitives to canonical Foundation before exposing an alias
- stop when forwarding changes payload bytes, hashes, validation, or outcome meaning
- escalate when a removal could make persisted documents unreadable through a supported path

## Review questions

- do both import paths produce identical stable representation
- is every alias symbol owned by a public canonical Foundation surface
- does the change preserve document and migration compatibility for consumers
