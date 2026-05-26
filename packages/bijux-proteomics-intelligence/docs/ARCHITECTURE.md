# Architecture

## Package identity

- Distribution name: `bijux-proteomics-intelligence`
- Import root: `bijux_proteomics_intelligence`

## Architectural role

`bijux-proteomics-intelligence` transforms core workflow state and
knowledge-owned evidence posture into explicit analytical judgment.

Its architecture is organized around six durable analytical families plus an
explicit governance family:

- `candidates`: `candidates/ranking.py`, `candidates/lifecycle.py`,
  `candidates/quality.py`, `candidates/validation.py`
- `judgment`: `judgment/policies.py`, `judgment/scenarios.py`,
  `judgment/recommendations.py`, `judgment/paths.py`
- `posture`: `posture/evidence.py`, `posture/skeptical.py`
- `interpretation`: `interpretation/runs.py`,
  `interpretation/quantitative.py`, `interpretation/ptm.py`,
  `interpretation/contaminants.py`, `interpretation/contrasts.py`,
  `interpretation/pathways.py`, `interpretation/structures.py`
- `reviews`: `reviews/boards.py`, `reviews/candidates.py`,
  `reviews/pathways.py`, `reviews/decision_briefs.py`, `reviews/benchmarks.py`
- `learning`: `learning/adaptation.py`, `learning/refinement/`
- `governance`: `governance/charter.py`

## Design constraints

- ranking policy is explicit and serializable
- every downgrade or refusal is accompanied by explicit evidence reasons
- scenario recommendations remain deterministic for fixed inputs and policy
- review outputs keep unresolved questions visible instead of hiding them

## Module topology

- `candidates/ranking.py` owns candidate framing, ranking narratives, and explainability summaries
- `candidates/lifecycle.py` owns candidate movement, risk, and portfolio lifecycle semantics
- `judgment/policies.py` owns ranking factors and policy contracts
- `judgment/scenarios.py` owns scenario evaluation and portfolio-facing judgment summaries
- `judgment/recommendations.py` owns recommendation refusal, escalation, uncertainty, and advisory-versus-enforced decision envelopes
- `judgment/paths.py` owns end-to-end analytical decision paths
- `posture/evidence.py` owns contradiction, freshness, downgrade, and refusal posture
- `posture/skeptical.py` owns explicit challenge pressure over recommendations
- `reviews/boards.py` owns board-facing review synthesis
- `reviews/candidates.py` owns candidate-facing review projections
- `reviews/pathways.py` owns pathway-facing review projections
- `reviews/decision_briefs.py` owns decision-brief assembly and ranked-evidence presentation
- `reviews/benchmarks.py` owns benchmark-backed release review claims
- `interpretation/runs.py`, `interpretation/quantitative.py`,
  `interpretation/ptm.py`, `interpretation/contaminants.py`,
  `interpretation/contrasts.py`, `interpretation/pathways.py`, and
  `interpretation/structures.py` own typed cautious interpretation contracts
- `learning/adaptation.py` and `learning/refinement/` own future-oriented learning pressure
- `governance/charter.py` owns the machine-readable capability map and charter

## Canonical tree layout

- Import roots: `bijux_proteomics_intelligence`
- Top-level families: `candidates/`, `claims/`, `governance/`, `interpretation/`, `judgment/`, `learning/`, `posture/`, `reviews/`
- Root modules: `belief_audit.py`, `contradictions.py`, `falsifiers.py`, `next_steps.py`, `public_api.py`, `query.py`, `refusal.py`

## Dependency direction

The package emphasizes auditable analytical judgment over broad convenience.

It may depend on core program state, knowledge evidence, and lab-facing
feasibility inputs, but it must not take ownership of scientific truth,
evidence curation, runtime orchestration, or laboratory scheduling.

## Downstream expectations

Downstream packages should treat this package as the canonical place for
ranking, downgrade, refusal, review, and cautious interpretation logic instead
of embedding shadow decision rules elsewhere.

## Extension signals

- add code here when a new concern changes analytical judgment meaning
- extend the owner module for the matching analytical band before widening the root API
- keep new downgrade or refusal logic here when it changes recommendation meaning

## Misplacement signals

- if the change needs scientific parsing, evidence storage, lab execution, or
  CLI/API transport wiring, it belongs in another package
- if a helper mainly reformats outputs for operator interfaces, it belongs in runtime
- if a rule only exists because one workflow wants a local override, keep it with that owner

## Review questions

- does the change modify analytical judgment meaning rather than just result transport
- would another package start carrying shadow ranking or refusal logic if this stayed out of intelligence
- can the package boundary still be described without claiming scientific truth,
  runtime execution, or lab orchestration authority
