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

## Escalation signals

- if a change defines candidate ranking, scenario evaluation, or explainable
  recommendation meaning, escalate it here before other packages improvise it
- if a proposed intelligence helper mainly owns lifecycle law, evidence truth,
  lab execution, or runtime delivery concerns, escalate it back to the owning
  package instead
- if scoring logic starts depending on operator entrypoints or transport-local
  payload shapes, treat that as a boundary failure and redesign the seam

## Review questions

- does the change alter recommendation semantics, scenario evaluation, or
  explainability rather than only how results are transported
- would runtime or lab code start carrying shadow scoring truth if this logic
  stayed out of intelligence
- can the change still be justified without claiming lifecycle, evidence,
  lab-execution, or runtime-interface ownership
