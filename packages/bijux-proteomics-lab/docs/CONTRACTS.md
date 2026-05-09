# Contracts

## Public package identity

- Distribution name: `bijux-proteomics-lab`
- Import root: `bijux_proteomics_lab`
- Stable entrypoints: `plan_experiment_batches`, `build_review_packet`,
  `build_advisory_assay_plan`, and `build_executable_assay_plan`

## Stable contracts

- planning contracts expose dependency order, queue pressure, capacity, and
  material feasibility
- readiness contracts expose blocked controls, provenance gaps, staffing or
  instrument limits, and workflow blockers
- handoff contracts preserve refusal behavior, operator-visible explanations,
  protocol controls, caveats, and lossy export notes
- reconciliation contracts preserve requested work, observed work, belief
  posture, and operational follow-through
- benchmark contracts keep supported, weakened, and blocked claims separate,
  and keep requested-versus-observed outcome dossiers plus assay-worth-it
  judgments explicit

## Change requirements

Any change to planning, readiness, refusal, reconciliation, or benchmark
posture should update the focused owner-family tests.

Changes that widen the public root or weaken handoff honesty need explicit
policy and docs updates.

## Consumer upgrade expectations

- downstream consumers should not need to rediscover why work was blocked,
  weakened, or refused
- operationally meaningful changes should appear through typed fields rather
  than only through free-form text
- consumers should expect the root surface to stay narrow while deeper
  operational contracts remain under owner bands

## Change routing signals

- route planning, readiness, refusal, and reconciliation contracts here first
- route analytical recommendation logic back to intelligence
- route core scientific semantics back to core or knowledge
- route execution orchestration or runtime policy back to runtime

## Validation checkpoints

- planning and readiness tests should make queue pressure, material limits, and
  blocked controls explicit
- handoff tests should preserve refusal codes, explanations, protocol controls,
  and lossy export reporting
- reconciliation and benchmark tests should preserve supported, weakened, and
  blocked follow-through
- contract changes should stay green in focused package and dev governance
  suites before release

## Review questions

- does the contract improve operational honesty, feasibility, or traceability
- can an operations reviewer still tell what was requested, what was blocked,
  and what actually happened
- can the contract still be justified without claiming analytical
  recommendation logic, core scientific semantics, or runtime policy ownership

## Explicit non-contracts

- This package does not define analytical recommendation logic.
- This package does not define core scientific semantics.
- This package does not define execution orchestration or runtime policy.
