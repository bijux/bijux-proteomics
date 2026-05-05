# Contracts

## Public package identity

- Distribution name: `bijux-proteomics-intelligence`
- Import root: `bijux_proteomics_intelligence`
- Canonical owner families: `candidates/`, `judgment/`, `posture/`,
  `reviews/`, `interpretation/`, `learning/`, and `governance/`
- Curated root compatibility namespaces: `benchmark_reviews`, `briefs`,
  `charter`, `decision_paths`, `evidence_posture`, `evaluators`,
  `follow_up_learning`, `interpretation`, `policies`, and
  `skeptical_review`

## Stable contracts

- ranking outputs include ordered candidates plus explicit rejection details
- evidence posture outputs include downgrade or refusal signals with machine-readable causes
- review outputs keep unresolved questions visible instead of replacing them with polished summaries
- interpretation outputs preserve caveats and explicit non-claims
- policy fields remain typed and reproducible for repeated evaluation

## Change requirements

Changes to ranking, downgrade, refusal, or interpretation behavior should be
accompanied by focused tests that make analytical differences explicit.

Contract changes should update the focused package tests that pin ranking,
review, contradiction handling, interpretation, or benchmark-review semantics.

## Consumer upgrade expectations

- downstream callers should be able to consume routine releases without
  rebuilding analytical namespace or packet parsing logic
- intentional ranking, refusal, or downgrade changes should be visible through
  explicit test updates and stable field naming
- consumers should expect rationale, refusal, and unresolved-question structures
  to remain typed and machine-readable

## Change routing signals

- ranking policy, recommendation readiness, skeptical review, and cautious
  interpretation belong here first
- scientific parsing, evidence truth, runtime orchestration, and lab scheduling
  should be routed back to their owning packages
- if higher layers need richer summaries, the durable contract change should
  start in the matching intelligence owner module before other layers reshape it

## Validation checkpoints

- ranking and scenario tests should make recommendation changes visible instead
  of burying them inside broad fixture churn
- contradiction, downgrade, and refusal tests should preserve explicit machine-readable causes
- interpretation tests should preserve typed caveats and stable summary fields
- contract changes should stay green in focused package tests before runtime or
  operator layers reshape the outputs

## Review questions

- does the contract change alter analytical judgment meaning rather than just output transport
- does it keep downgrade, refusal, and unresolved-question behavior explicit
- can the contract still be justified without claiming scientific truth,
  runtime-interface, or lab-execution ownership

## Explicit non-contracts

- This package does not define workflow-stage law or lifecycle gate authority.
- This package does not own evidence persistence, contradiction storage, or curation truth.
- This package does not own laboratory scheduling, runtime transport, or batch execution logic.
