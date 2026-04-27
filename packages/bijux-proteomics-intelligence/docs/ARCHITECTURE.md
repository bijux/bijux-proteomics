# Architecture

## Package identity

- Distribution name: `bijux-proteomics-intelligence`
- Import root: `bijux_proteomics_intelligence`

## Architectural role

`bijux-proteomics-intelligence` transforms program and evidence context into
explainable candidate decisions.

## Design constraints

- ranking policy is explicit and serializable
- every rejection is accompanied by structured reason codes
- scenario recommendations are deterministic for a fixed policy and inputs

## Module topology

- `briefs.py` owns candidate framing, ranking narratives, and explainability summaries
- `policies.py` owns ranking factors, metric catalogs, and decision policy models
- `evaluators.py` owns scenario, progression, redesign, and portfolio evaluation
- `candidates.py` owns candidate selection, transition, and risk-profile helpers
- `outcomes.py` owns rejection outputs and tie-break explanations

## Dependency direction

The package emphasizes auditability over opaque scoring.

It may depend on core program state and knowledge summaries, but it should not
take ownership of lifecycle authority, evidence persistence, or laboratory
execution semantics.

## Downstream expectations

Downstream packages should treat this package as the canonical place for
ranking and recommendation logic instead of embedding ad hoc scoring formulas
inside runtime or lab helpers.
