# Boundaries

## Package identity

- Distribution name: `bijux-proteomics-intelligence`
- Import root: `bijux_proteomics_intelligence`

## This package owns

- design brief generation from core program state
- candidate ranking, filtering, and rejection semantics
- scenario and portfolio evaluation logic
- explainability and risk summary outputs

## This package does not own

- canonical program entity definitions
- evidence persistence and contradiction handling contracts
- assay scheduling and execution feedback workflows

## Dependency direction

This package may depend on foundation primitives, core program state, and
knowledge summaries when it computes rankings or scenario recommendations.

It should not become the canonical owner of lifecycle authority, evidence
storage, or lab execution semantics.

## Downstream expectations

Downstream packages should treat this package as the home of recommendation
policy and explainability outputs, not as a generic place to stash scoring
helpers beside unrelated runtime or domain code.
