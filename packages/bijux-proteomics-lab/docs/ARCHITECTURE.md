# Architecture

## Package identity

- Distribution name: `bijux-proteomics-lab`
- Import root: `bijux_proteomics_lab`

## Architectural role

`bijux-proteomics-lab` is the operational product for wet-lab follow-up. It
receives scientific intent from lower packages, then decides whether that work
is executable under real queue pressure, material limits, controls, and handoff
constraints.

## Design constraints

- execution reality beats analytical enthusiasm
- queue pressure, material scarcity, blocked controls, and provenance gaps stay
  first-class data instead of narrative footnotes
- refusals stay explicit and machine-readable
- observed outcomes must trace back to requested work

## Module topology

- `planning/assays.py` owns batch construction, dependency order, review
  packets, and executable request assembly
- `planning/scheduling.py` owns capacity fitting, scenario comparison, and
  material-feasibility ordering
- `planning/priorities.py` owns information-gain scoring, practicality
  screening, and cycle briefs
- `planning/next_cycle.py` owns contradiction resolution, orthogonal
  confirmation, and next-cycle recommendation
- `design/experiments.py` and `design/protocols.py` own design validation,
  sample layout, protocol versions, controls, and failure caveats that make
  later handoffs credible
- `readiness/operations.py` and `readiness/stages.py` own material, controls,
  provenance, backlog, staffing, instrument, and stage readiness
- `lifecycle/progression.py` owns operational progression and follow-up
  validation after planning and readiness are known
- `handoffs/transitions.py` owns transition-level readiness and approval
- `handoffs/explanations.py` owns refusal behavior and operator-facing handoff
  honesty
- `handoffs/exports.py` owns lossy exports and alternative-plan comparisons
- `handoffs/risk.py` and `handoffs/ptm.py` own assay-risk and PTM-specific
  follow-up controls
- `outcomes/observations.py` owns observed assay results and rerun posture
- `reconciliation/follow_up.py` owns requested-versus-observed traceability and
  downstream feedback posture
- `benchmarks/claims.py` and `benchmarks/rehearsals.py` own targeted
  operational claim support and rehearsal delivery
- `benchmarks/follow_up.py` owns the planned flagship assay boundary, and
  `benchmarks/outcome_dossiers.py` owns the requested-versus-observed flagship
  outcome dossiers plus the cross-family assay-worth-it ledgers
- `governance/` owns the machine-readable lab charter and owner-map boundaries
  for operational planning, readiness, handoff, and reconciliation surfaces

## Canonical tree layout

- Import roots: `bijux_proteomics_lab`
- Top-level families: `benchmarks/`, `design/`, `governance/`, `handoffs/`, `lifecycle/`, `outcomes/`, `planning/`, `readiness/`, `reconciliation/`
- Root modules: `public_api.py`

## Dependency direction

The package may depend on core, knowledge, and intelligence inputs to
understand what operators are being asked to do.

It must not become the owner of analytical recommendation logic, core
scientific semantics, or runtime execution orchestration or policy.

## Downstream expectations

Downstream packages should use this layer when they need a credible answer to
whether work can run, should be refused, or changed belief posture after it
ran. They should not duplicate queue-pressure logic, handoff refusal logic, or
requested-versus-observed reconciliation elsewhere.

## Extension signals

- add code here when a change alters operational feasibility, handoff honesty,
  or observed follow-through
- extend the existing owner families before adding new flat compatibility
  surfaces
- keep new operational policies close to the owner that can refuse or downgrade
  the work

## Misplacement signals

- if the change mostly ranks candidates, justifies a recommendation, or
  interprets scientific truth, it does not belong here
- if the change mostly dispatches runs, binds providers, or shapes route
  transport, it belongs in runtime
- if the change mainly preserves compatibility wrappers, it should not widen
  durable lab ownership

## Review questions

- does the architecture still optimize for operational honesty, feasibility,
  and traceability
- would operators lose queue-pressure, material-limit, or refusal context if
  this behavior moved elsewhere
- can the package still be explained without claiming analytical recommendation
  logic, core scientific semantics, or runtime policy ownership
