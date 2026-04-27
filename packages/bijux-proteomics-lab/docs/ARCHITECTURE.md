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

- `planning.py` owns dependency-aware planning, scheduling, and next-cycle logic
- `outcomes.py` owns execution outcome interpretation and rerun policy support
- `repositories.py` owns queue, feedback, and forecast repository contracts
- `schema.py` owns lab artifact schema contracts and upgrade advice
- `serialization.py` owns canonical artifact envelopes and payload comparison

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
- extend `planning.py`, `outcomes.py`, or `repositories.py` before runtime or
  intelligence code invents local scheduling helpers
- keep new operational decision rules here when they define lab behavior rather
  than only the way results are exposed to operators

## Misplacement signals

- if the change needs lifecycle authority, evidence truth, ranking policy, or
  transport-bound interface logic, it belongs in another package
- if a helper mainly reformats planning or outcome data for CLI or API surfaces,
  it belongs in runtime adapters instead of lab modules
- if a rule only exists for one recommendation or evidence flow, keep it with
  that owner instead of widening lab semantics
