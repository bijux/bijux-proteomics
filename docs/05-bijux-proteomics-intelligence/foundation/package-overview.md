---
title: Decision Intelligence Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Decision intelligence map

The intelligence package is a collection of explicit decision stages. It
keeps ranking mechanics, scientific interpretation, skeptical challenge,
policy judgment, and learning separate so a change in one can be reviewed
without silently changing the others.

```mermaid
flowchart LR
    question["decision question"]
    candidates["candidate universe\nincluding exclusions"]
    interpretation["bounded scientific interpretation"]
    challenge["support · contradiction · falsifier"]
    policy["named scenario and policy"]
    disposition["recommend · hold · downgrade · refuse"]
    review["human or explicitly promoted authority"]
    question --> candidates --> interpretation --> challenge --> policy --> disposition --> review
```

The package owns the recorded argument between question and disposition. It
does not own the source evidence, execute proteomics analyses, or grant the
experimental authority shown at the right edge.

## Candidate construction

`candidates` defines candidate records and schemas, validation, transformations,
filters, quality signals, fingerprints, lifecycle state, persistent stores,
ranking, and final selection. A ranking is meaningful only relative to the
candidate set it considered; excluded and invalid candidates remain part of the
audit trail.

## Interpretation

`interpretation` provides bounded readings of runs, quantitative results,
contrasts, pathways, PTMs, contaminants, and structures. These modules translate
scientific outputs into features and statements suitable for decisions. They
do not replace core calculations or knowledge grounding.

## Skeptical pressure

`claims` evaluates support, `contradictions` finds incompatible assertions, and
`falsifiers` formulates evidence that could overturn a position. `posture`
records whether the assembled evidence is strong, weak, conflicting, or
otherwise unsuitable for a decisive recommendation.

```mermaid
flowchart TD
    interpretation["bounded interpretation"]
    support["claim support"]
    contradiction["contradictions"]
    falsifier["falsifiers"]
    posture["evidence posture"]
    interpretation --> support --> posture
    interpretation --> contradiction --> posture
    interpretation --> falsifier --> posture
```

## Judgment

`judgment` contains the policy-bearing surface: scenarios, recommendation
rules, benchmark policies, confidence, decision packets, blinded challenges,
counterfactuals, sensitivity, quality, and regret. The output is a
recommendation record with enough context to explain why another policy or
scenario could produce a different answer.

`reviews` exposes that reasoning for scrutiny through workflow-specific
benchmark reviews, boards, candidate reviews, independent-rerun checks,
decision briefs, external review kits, outsider packets, release candidates,
and public-scrutiny reports.

## Inspect A Recommendation By Question

| Question | Owning surface | Evidence to inspect |
| --- | --- | --- |
| Which alternatives entered or left the comparison? | `candidates` | input fingerprint, validation, exclusions, transformations, lifecycle state |
| Which scientific meaning was extracted from the inputs? | `interpretation` | bounded feature or statement plus the source record it projects |
| What could defeat the preferred answer? | `claims`, `contradictions`, `falsifiers`, `posture` | adverse evidence, severity, missing support, falsification condition |
| Why did one action outrank another? | `judgment` | scenario, policy identity, weights, gates, tie handling, decisive criteria |
| Would a plausible assumption change the answer? | counterfactual, sensitivity, and regret surfaces | alternate policy result, rank stability, observed cost |
| Who may act on the result? | decision envelope and external authority | advisory/enforced state, promoting actor, rationale, human-review requirement |

## Learning without rewriting history

`learning` adapts future policy from review and outcome signals. Refinement
tracks convergence and stagnation explicitly. Historical evidence,
recommendations, and outcomes remain immutable inputs to the later learning
record; learning must not retroactively make an earlier decision appear better
calibrated than it was.

## Public surface

The root package exposes module families rather than a broad collection of
functions:

```python
from bijux_proteomics_intelligence import (
    candidates,
    interpretation,
    judgment,
    posture,
    refusal,
    reviews,
)
```

This is a library package without a standalone CLI or HTTP service. Runtime can
expose intelligence-backed routes while retaining ownership of transport and
execution behavior.

## Non-goals

Intelligence does not curate literature, resolve biological identifiers, run
mass-spectrometry workflows, or schedule assays. It consumes those owned
artifacts and returns a policy decision. When evidence, reproducibility, or lab
feasibility is insufficient, the correct result is a downgrade or refusal.

A review is incomplete if it reports the selected candidate without the
candidate universe, or reports confidence without the policy, adverse
evidence, sensitivity, and authority state that produced it.
