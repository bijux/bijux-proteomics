# Boundaries

## Package identity

- Distribution name: `bijux-proteomics-lab`
- Import root: `bijux_proteomics_lab`

## This package owns

- dependency-aware planning that exposes queue pressure, family capacity, and
  material limits
- readiness checks that keep controls, provenance, staffing, backlog, and
  instrument gaps explicit before spend is committed
- handoff honesty, including refusal behavior, blocked explanations, and lossy
  export notes
- observed-outcome reconciliation that compares requested work with observed
  work and records supported, weakened, or blocked follow-through
- targeted operational benchmark rehearsals that prove whether a claimed lab
  story is supportable

## This package does not own

- analytical recommendation logic
- core scientific semantics
- execution orchestration or runtime policy

## Dependency direction

This package may depend on lower layers for scientific intent and evidence
inputs, but it must keep ownership scoped to operational feasibility and
traceability.

It should never become the package that decides what is scientifically true,
what candidate should be recommended, or how runtime dispatch executes the
work.

## Downstream expectations

Downstream packages should import owner bands such as `planning`, `readiness`,
`handoffs`, `outcomes`, `reconciliation`, and `benchmarks` when they need lab
behavior. They should not treat `bijux_proteomics_lab` as a broad catalog or
reimplement refusal and feasibility logic locally.

## Escalation signals

- if a change reinterprets scientific meaning, recommendation policy, or
  lifecycle law, escalate it back to core, knowledge, or intelligence
- if a change introduces provider binding, scheduler policy, route transport,
  or runtime orchestration, escalate it to runtime
- if a change makes blocked work look executable by hiding queue pressure,
  material limits, or missing controls, stop and redesign the seam

## Review questions

- does the change preserve explicit queue pressure, material limits, and
  handoff honesty
- would an operations reviewer still understand why work is blocked, downgraded,
  or safe to execute
- can the boundary still be justified without claiming analytical
  recommendation logic, core scientific semantics, or runtime policy ownership
