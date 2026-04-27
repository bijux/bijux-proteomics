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
