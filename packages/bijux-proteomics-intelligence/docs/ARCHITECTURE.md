# Architecture

## Package identity

- Distribution name: `bijux-proteomics-intelligence`
- Import root: `bijux_proteomics_intelligence`

## Architectural role

`bijux-proteomics-intelligence` transforms core workflow state and
knowledge-owned evidence posture into explicit analytical judgment.

Its architecture is organized around five durable analytical bands:

- `candidates`: `candidates/ranking.py`, `candidates/lifecycle.py`
- `judgment`: `judgment/policies.py`, `judgment/scenarios.py`,
  `judgment/recommendations.py`, `judgment/paths.py`
- `posture`: `posture/evidence.py`, `posture/skeptical.py`
- `interpretation`: `interpretation/summaries.py`
- `reviews`: `reviews/analysis.py`, `reviews/packets.py`,
  `reviews/benchmarks.py`
- `learning`: `learning/adaptation.py`, `learning/iterative_design/`
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
- `reviews/packets.py` owns review packet assembly and ranked-evidence presentation
- `reviews/analysis.py` owns downstream analytical review projections
- `reviews/benchmarks.py` owns benchmark-backed release review claims
- `interpretation/summaries.py` owns typed cautious interpretation contracts
- `learning/adaptation.py` and `learning/iterative_design/` own future-oriented learning pressure
- `governance/charter.py` owns the machine-readable capability map and charter

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
