# Architecture

## Package identity

- Distribution name: `bijux-proteomics-intelligence`
- Import root: `bijux_proteomics_intelligence`

## Architectural role

`bijux-proteomics-intelligence` transforms core workflow state and
knowledge-owned evidence posture into explicit analytical judgment.

Its architecture is organized around five durable analytical bands:

- `judgment`: `briefs.py`, `policies.py`, `evaluators.py`, `recommendations.py`, `candidates.py`
- `evidence_posture`: `evidence_posture.py`
- `interpretation`: `interpretation.py`, `analytical_review.py`
- `review`: `decision_paths.py`, `review_packets.py`, `skeptical_review.py`, `benchmark_reviews.py`
- `learning`: `follow_up_learning.py`, `design_loop/`

## Design constraints

- ranking policy is explicit and serializable
- every downgrade or refusal is accompanied by explicit evidence reasons
- scenario recommendations remain deterministic for fixed inputs and policy
- review outputs keep unresolved questions visible instead of hiding them

## Module topology

- `briefs.py` owns candidate framing, ranking narratives, and explainability summaries
- `policies.py` owns ranking factors and policy contracts
- `evidence_posture.py` owns contradiction, freshness, downgrade, and refusal posture
- `evaluators.py` owns scenario evaluation and portfolio-facing judgment summaries
- `recommendations.py` owns recommendation refusal, escalation, uncertainty, and advisory-versus-enforced decision envelopes
- `review_packets.py` owns review packet assembly and ranked-evidence presentation
- `decision_paths.py` owns end-to-end analytical decision paths
- `skeptical_review.py` owns explicit challenge pressure over recommendations
- `benchmark_reviews.py` owns benchmark-backed release review claims
- `interpretation.py` and `analytical_review.py` own typed cautious interpretation
- `follow_up_learning.py` and `design_loop/` own future-oriented learning pressure

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
