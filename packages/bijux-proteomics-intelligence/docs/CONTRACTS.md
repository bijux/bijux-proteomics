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

## Consumer upgrade expectations

- downstream callers should be able to consume routine releases without
  rebuilding candidate, brief, or outcome parsing logic
- intentional scoring or explainability changes should be visible through
  explicit test updates and stable field naming
- consumers should expect rejection and rationale structures to remain typed and
  machine-readable

## Change routing signals

- ranking policy, candidate ordering, and recommendation rationale belong here
  first
- lifecycle authority, evidence truth, and lab scheduling should be routed back
  to their owning packages instead of being embedded in scoring helpers
- if runtime or compat surfaces need richer operator summaries, the durable
  change should start here before higher layers reshape the outputs

## Explicit non-contracts

- This package does not define lifecycle gate authority.
- This package does not own evidence persistence or contradiction storage.
- This package does not own laboratory scheduling or batch execution logic.
