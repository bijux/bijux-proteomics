---
title: bijux-proteomics-intelligence
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# bijux-proteomics-intelligence

`bijux-proteomics-intelligence` turns scientific evidence and program
constraints into inspectable decisions. It owns candidate ranking, scenario
analysis, skeptical challenge, recommendation posture, and refusal. It does not
own the evidence it evaluates.

```bash
python -m pip install bijux-proteomics-intelligence
```

## Decision pipeline

```mermaid
flowchart LR
    evidence["evidence and execution records"]
    candidates["candidate set\nfilter · validate · fingerprint"]
    rank["ranking\npolicy · quality · selection"]
    challenge["challenge\ncontradictions · falsifiers · scenarios"]
    judgment["judgment\nsensitivity · confidence · regret"]
    result{"supported?"}
    recommend["recommendation record"]
    refuse["refusal with reasons"]
    evidence --> candidates --> rank --> challenge --> judgment --> result
    result -->|yes| recommend
    result -->|no| refuse
```

Every recommendation is a policy output, not a fact. Its candidate set,
policy, evidence posture, sensitivity, alternatives, and reason codes remain
recoverable so a reviewer can reproduce the judgment without treating the
result as new evidence.

## Recommendation record anatomy

| Field | Why it matters |
| --- | --- |
| candidate universe and exclusions | prevents a winning candidate from being presented without the alternatives it defeated |
| evidence references and fingerprints | ties the decision to immutable review inputs without copying or rewriting them |
| policy and constraints | exposes the values, thresholds, feasibility limits, and objectives that shaped the ranking |
| score components and ordering | makes aggregation and tie-breaking inspectable |
| contradictions and falsifiers | records evidence that weakens or could overturn the action |
| scenarios and sensitivity | shows whether small plausible changes reverse the ranking |
| confidence and regret | separates certainty language from the estimated cost of being wrong |
| posture and human-review flag | distinguishes advisory output, downgrade, escalation, and refusal |

## Analytical capabilities

| Surface | Responsibility |
| --- | --- |
| `candidates` | typed records, validation, filtering, quality, fingerprints, ranking, selection, storage, and lifecycle |
| `interpretation` | quantitative, contrast, pathway, PTM, contaminant, structure, and run-level readings |
| `claims`, `contradictions`, `falsifiers` | support checks and skeptical pressure against an interpretation |
| `judgment` | policies, scenarios, recommendations, blinded challenges, counterfactuals, sensitivity, confidence, regret, and flagship decisions |
| `posture` | explicit evidence posture and skeptical review |
| `reviews` | benchmark reviews, review boards, decision briefs, outsider packets, independent reruns, and public scrutiny |
| `learning` | adaptation, refinement convergence, and stagnation detection |
| `next_steps`, `query`, `refusal` | action handoff, interrogation, and unsupported-claim refusal |

The package root lazily exposes these fourteen owner modules, keeping import
cost and accidental coupling low while making the supported capability families
discoverable.

## What makes a recommendation defensible

A recommendation is strongest when:

1. the candidate set and exclusions are explicit;
2. the ranking policy and input evidence are fingerprinted;
3. plausible contradictory evidence and falsifiers were evaluated;
4. ranking stability survives threshold and scenario sensitivity;
5. competing actions and the cost of error are visible;
6. confidence is calibrated against benchmark and observed outcome evidence;
7. a refusal remains possible when the support is inadequate.

Benchmark review modules cover DDA, DIA, PTM, quantification, and targeted
workflow families. Their existence does not grant equal authority to every
family; the recommendation record inherits the evidence ceiling of the input
benchmark and review packet.

## Decision stability

| Observed behavior | Interpretation | Required posture |
| --- | --- | --- |
| ordering survives plausible thresholds and evidence removal | locally stable under tested pressure | bounded recommendation with tested conditions |
| top candidates exchange rank under small changes | policy-sensitive | expose alternatives and require review |
| recommendation depends on one contested source | evidence-fragile | downgrade until contradiction is resolved |
| feasible action changes when assay burden is included | consequence-sensitive | return cost and burden to the decision record |
| no candidate satisfies hard constraints | unsupported action | refuse with unmet conditions |

Stability applies only to the tested candidate universe, evidence snapshot,
policy, and scenario set. It does not imply that an omitted candidate or future
evidence could not change the result.

## Challenge before action

```mermaid
flowchart TD
    R["ranked candidates"] --> B["blinded evidence challenge"]
    B --> C["counterfactual scenarios"]
    C --> S["threshold sensitivity"]
    S --> G["regret analysis"]
    G --> D{"ranking remains defensible?"}
    D -->|yes| P["bounded recommendation"]
    D -->|weakens| W["downgrade or escalate"]
    D -->|no| F["refuse"]
```

A recommendation that changes under a plausible threshold, withheld evidence
pattern, or feasible alternative must expose that instability. Explanation is
not a substitute for challenge; it reports how the declared policy behaved
under challenge.

## Ownership boundary

- Core owns scientific calculations and benchmark contracts.
- Runtime owns what executed and whether it can be replayed.
- Knowledge owns sources, claims, provenance, and contradiction state.
- Intelligence owns how reviewed inputs become a ranked or refused action.
- Lab owns whether that action is feasible and what happened after execution.

Intelligence may consume all of those signals, but it must not rewrite them.
Outcome-aware learning creates a new policy or calibration record rather than
editing the historical recommendation.

## Human authority boundary

Intelligence can rank, challenge, downgrade, or refuse an action. It does not
approve clinical use, spend resources, authorize an executable laboratory
handoff, or override biosafety and operational custody. A `human_review` flag
is a required decision state, not a claim that human review has occurred.

```mermaid
flowchart LR
    R["recommendation record"] --> H{"human and domain review"}
    H -->|revise| I["new policy or evidence input"]
    H -->|reject| X["closed or refused action"]
    H -->|accept advisory| L["Lab readiness assessment"]
    L -->|not ready| N["revised or refused plan"]
    L -->|ready and authorized| E["executable handoff"]
```

## Shared Reader Routes

- [Product Overview](../01-bijux-proteomics/foundation/product-overview.md)
  places recommendations in the full evidence-to-action system.
- [Workflow Consequence Maps](../01-bijux-proteomics/foundation/workflow-consequence-maps.md)
  trace how family-specific evidence changes downstream decisions.
- [What Changed The Recommendation](../01-bijux-proteomics/foundation/what-changed-the-recommendation.md)
  explains how to compare decision records without erasing history.
- [Lab Consequence](../07-bijux-proteomics-lab/foundation/lab-consequence.md)
  bounds the operational effect of advisory output.

## Start Inside

- [Package overview](foundation/package-overview.md) describes analytical
  modules and artifact flow.
- [Recommendation challenges](foundation/workflow-recommendation-challenges.md)
  covers blinded, counterfactual, and family-specific pressure.
- [Recommendation confidence](foundation/workflow-recommendation-confidence.md)
  covers calibration, overconfidence, underconfidence, and regret.
- [Architecture](architecture/index.md) explains policy and dependency
  boundaries.
- [Interfaces](interfaces/index.md) documents Python, data, and artifact
  contracts.
- [Known limitations](quality/known-limitations.md) records where decision
  authority remains bounded.
