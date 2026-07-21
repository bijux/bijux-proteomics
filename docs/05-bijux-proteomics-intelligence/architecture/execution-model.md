---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Execution Model

An intelligence evaluation is a recorded argument, not an opaque score. It starts with a decision question and candidate set, binds the relevant evidence, applies declared policy, actively searches for reasons to withhold confidence, and emits a reviewable recommendation or refusal.

```mermaid
flowchart LR
    Q[Decision question] --> V[Validate candidates]
    V --> E[Bind evidence and posture]
    E --> C[Challenge contradictions and falsifiers]
    C --> S[Evaluate scenario and policy]
    S --> D{Decision support outcome}
    D -->|supported| R[Rank and recommend]
    D -->|insufficient| F[Refuse or request evidence]
    R --> P[Review packet]
    F --> P
```

## Evaluation stages

Candidate validation establishes identity, comparable fields, quality, and lifecycle state. Evidence posture records what kinds of support are present and how directly they bear on the decision. Contradiction and falsifier passes expose adverse evidence before ranking rather than appending caveats afterward.

Judgment then applies an explicit policy in a named scenario. Ranking is meaningful only within that policy: weights, gates, uncertainty treatment, and ties are part of the result. A recommendation must retain the candidate fingerprint, evidence references, policy identity, decisive criteria, sensitivity, and reasons alternatives were not selected.

## Review path

```mermaid
sequenceDiagram
    participant Caller
    participant Eval as Candidate evaluation
    participant Challenge as Skeptical challenge
    participant Policy as Judgment policy
    participant Review as Review projection
    Caller->>Eval: question, candidates, evidence refs
    Eval->>Challenge: validated comparison
    Challenge->>Policy: support plus adverse evidence
    Policy->>Review: recommendation or refusal
    Review-->>Caller: brief, audit, next steps
```

Decision briefs and outsider packets make the same reasoning available at different review depths. Independent-rerun and benchmark modules test whether the outcome can be reproduced and whether policy behavior remains calibrated across blinded cases, counterfactuals, sensitivity changes, and regret analyses.

## Learning without silent drift

Outcome feedback may propose adaptation, but it cannot rewrite an active decision retroactively or mutate policy invisibly. Learning records connect reviewed outcomes to a declared policy change. Existing packets retain the policy and evidence snapshot under which they were produced, so later improvements do not erase the historical basis of a decision.
