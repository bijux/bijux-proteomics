# Architecture

## Package identity

- Distribution name: `bijux-proteomics-knowledge`
- Import root: `bijux_proteomics_knowledge`

## Architectural role

`bijux-proteomics-knowledge` provides the evidence-centric domain for decision
traceability: claims, bundles, trust scoring, contradictions, and lineage.

## Design constraints

- evidence records are first-class typed entities
- contradiction handling is policy-based and explicit
- trust, freshness, and context completeness are measurable outputs

## Module topology

- `evidence.py` owns bundles, trust scoring, freshness, and contradiction inputs
- `claims.py` owns claim state, lineage, and knowledge-gap modeling
- `resolution.py` owns explicit conflict-resolution policies and updates
- `graph.py` owns evidence-graph structure and validation
- `review.py` owns decision-readiness and review-packet synthesis

## Dependency direction

The package is designed to keep decision rationale inspectable.

It may depend on foundation primitives and core identifiers, but it should not
take ownership of lifecycle authority, ranking policy, or lab execution logic.

## Downstream expectations

Downstream packages should use these evidence and resolution models directly
instead of maintaining separate trust, contradiction, or lineage formats.

## Extension signals

- add code here when a new concern changes evidence, claim, contradiction, or
  lineage semantics
- extend `evidence.py`, `claims.py`, `resolution.py`, `graph.py`, or `review.py`
  before downstream packages create shadow trust models
- keep new auditability rules here when they define evidence meaning rather than
  only how a runtime or recommendation surface displays it

## Misplacement signals

- if the change needs lifecycle authority, ranking policy, lab scheduling, or
  transport-bound payload shaping, it belongs elsewhere
- if a helper mainly reformats evidence results for API or CLI consumers, it
  belongs in runtime adapters rather than in knowledge models
- if a rule only exists to serve one scoring or lab flow, keep it with that
  owner instead of making knowledge absorb workflow-specific behavior
