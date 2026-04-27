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

## Extension signals

- add code here when a new concern changes ranking policy, explainability, or
  candidate-evaluation semantics
- extend `policies.py`, `evaluators.py`, `briefs.py`, or `outcomes.py` before
  runtime or lab code invents local scoring helpers
- keep new recommendation logic here when it changes decision meaning rather
  than only the way results are transported

## Misplacement signals

- if the change needs lifecycle authority, evidence persistence, lab execution,
  or CLI/API transport wiring, it belongs in another package
- if a helper mainly reformats intelligence outputs for operator interfaces, it
  belongs in runtime adapters instead of recommendation modules
- if a rule only exists because one lab workflow wants a local override, keep it
  with the owning workflow instead of broadening intelligence semantics

## Review questions

- does the change modify canonical ranking policy, explainability, or
  candidate-evaluation meaning rather than just result transport
- would runtime or lab code start carrying local scoring truth if this behavior
  were not owned here
- can the package boundary still be described without claiming lifecycle,
  evidence, or execution orchestration authority
