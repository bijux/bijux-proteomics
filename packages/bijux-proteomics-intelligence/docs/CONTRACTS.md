# Contracts

## Public package identity

- Distribution name: `bijux-proteomics-intelligence`
- Import root: `bijux_proteomics_intelligence`
- Stable entrypoints: `briefs`, `policies`, `evaluators`, `candidates`, and `outcomes`

## Stable contracts

- ranking outputs include ordered candidates plus explicit rejection details
- policy fields are stable and typed for reproducible evaluations
- scenario summaries expose action, confidence, and rationale data

## Change requirements

Changes to scoring or gating behavior should be accompanied by tests that make
decision differences explicit.

Contract changes should update the focused package tests that pin ranking,
scenario, explainability, or rejection semantics.

## Explicit non-contracts

- This package does not define lifecycle gate authority.
- This package does not own evidence persistence or contradiction storage.
- This package does not own laboratory scheduling or batch execution logic.
