# Architecture

## Package identity

- Distribution name: `bijux-proteomics-lab`
- Import root: `bijux_proteomics_lab`

## Architectural role

`bijux-proteomics-lab` turns planning constraints into concrete assay batches
and interprets execution outcomes back into decision-support artifacts.

## Design constraints

- planning uses explicit dependencies and capacity constraints
- review and progression outputs are structured and auditable
- outcome triage and rerun guidance are explicit policy outputs

## Module topology

- `planning/assays.py` owns dependency-aware planning, scheduling, review
  packets, and next-cycle logic
- `design/experiments.py` and `design/protocols.py` own experiment-design and
  protocol-preparation semantics needed before execution can be scheduled
- `readiness/operations.py` and `readiness/workflow.py` own readiness and
  blocker summaries before spend is committed
- `lifecycle/progression.py` owns progression and skeptical handoff validation
- `handoffs/packets.py`, `handoffs/artifacts.py`, `handoffs/risk.py`, and
  `handoffs/ptm.py` own reviewable packet, artifact, and risk semantics for
  lab-facing handoffs
- `outcomes/observations.py` owns execution outcome interpretation and rerun
  policy support
- `reconciliation/follow_up.py` owns feedback loops from observed outcomes back
  into future operational follow-up
- `benchmarks/targeted.py` owns targeted benchmark rehearsals that prove lab
  claims without widening the package root
- `repositories.py` owns queue, feedback, and forecast repository contracts
- the package root only exposes four durable entrypoints for batch planning and
  review-packet construction

## Dependency direction

The package acts as the operational bridge between decision intent and wet-lab
execution planning.

It may depend on core state, knowledge evidence, and intelligence outputs, but
it should not take ownership of lifecycle authority, ranking policy, or
evidence truth semantics.

## Downstream expectations

Downstream packages should rely on this layer for planning and outcome logic
instead of encoding assay scheduling or rerun semantics inside runtime flows.

## Extension signals

- add code here when a new concern changes planning, batching, outcome
  interpretation, or repository contracts for laboratory work
- extend the owner bands above before runtime or intelligence code invents
  local scheduling helpers
- keep new operational decision rules here when they define lab behavior rather
  than only the way results are exposed to operators

## Misplacement signals

- if the change needs lifecycle authority, evidence truth, ranking policy, or
  transport-bound interface logic, it belongs in another package
- if a helper mainly reformats planning or outcome data for CLI or API surfaces,
  it belongs in runtime adapters instead of lab modules
- if a rule only exists for one recommendation or evidence flow, keep it with
  that owner instead of widening lab semantics

## Review questions

- does the change alter canonical planning, batching, outcome interpretation,
  or lab repository behavior rather than just exposing those results
- would runtime or intelligence code start carrying local scheduling or rerun
  truth if this behavior stayed out of lab
- can the architecture still be explained without claiming lifecycle, evidence,
  ranking, or transport-bound interface ownership
