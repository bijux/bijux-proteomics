# Architecture

`bijux-proteomics-lab` turns planning constraints into concrete assay batches
and interprets execution outcomes back into decision-support artifacts.

Core design choices:

- planning uses explicit dependencies and capacity constraints
- review and progression outputs are structured and auditable
- outcome triage and rerun guidance are explicit policy outputs

The package acts as the operational bridge between decision intent and wet-lab
execution planning.
