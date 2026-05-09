# Boundaries

## Package identity

- Distribution name: `bijux-proteomics-intelligence`
- Import root: `bijux_proteomics_intelligence`

## This package owns

- candidate ranking, rejection semantics, and policy-governed explainability
- downgrade and refusal posture when evidence is stale, thin, or contradictory
- decision briefs, skeptical challenge pressure, and benchmark-backed review claims
- cautious interpretation summaries over already-typed proteomics evidence
- learning pressure that changes future prioritization without rewriting past decisions

## This package does not own

- canonical scientific entity definitions or parsing
- evidence storage, curation, and truth maintenance
- runtime orchestration, transport, or provider selection
- assay scheduling, execution authority, or operational queue ownership

## Dependency direction

This package may depend on foundation primitives, core workflow state,
knowledge-owned evidence, and lab feasibility inputs when it computes analytical
judgment.

It should not become the canonical owner of scientific truth, evidence
maintenance, runtime execution, or laboratory scheduling.

## Downstream expectations

Downstream packages should treat this package as the home of recommendation
meaning, downgrade thresholds, refusal posture, and cautious interpretation.

They should not expect this package to approve workflows unconditionally. When
evidence posture is weak, the package is expected to downgrade confidence, hold
recommendations, or refuse progression-oriented claims outright.

## Escalation signals

- if a change defines candidate ranking, refusal posture, review challenge
  pressure, or cautious interpretation meaning, escalate it here first
- if a proposal claims scientific truth, evidence ownership, runtime execution,
  or lab scheduling authority, escalate it back to the owning package
- if analytical code starts depending on package roots or transport-local
  payload shapes, treat that as a boundary failure and redesign the seam

## Review questions

- does the change alter analytical judgment semantics rather than only how results are transported
- does the change keep downgrade and refusal behavior explicit when evidence posture weakens
- can the change still be justified without claiming scientific truth,
  runtime-interface, or lab-execution ownership
