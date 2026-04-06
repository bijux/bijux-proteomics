# Contracts

Package contracts:

- lifecycle transitions are valid only through declared stage rules
- review gate decisions are deterministic for a given gate state and evidence
- identifier and setup validators produce explicit issue codes
- runtime adapters remain replaceable through protocol contracts

Downstream packages may consume these contracts, but should not bypass them.
