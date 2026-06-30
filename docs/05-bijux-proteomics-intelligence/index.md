---
title: bijux-proteomics-intelligence
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-06-30
---

# bijux-proteomics-intelligence

`bijux-proteomics-intelligence` owns decision policy in
`bijux-proteomics`. It turns evidence and program constraints into scores,
rankings, scenarios, and explanations that remain inspectable instead of
pretending to be upstream fact. This is where the system stops only describing
the world and starts making judgments about what should happen next.

This package is also more concrete now than older docs suggested. It is not a
vague "decision layer." It owns recommendation posture, benchmark-backed
challenge routes, confidence and regret surfaces, interpretation summaries, and
learning-facing judgment that stays visibly separate from scientific truth.

```mermaid
flowchart LR
    foundation["foundation<br/>shared meaning"]
    core["core<br/>durable rules"]
    knowledge["knowledge<br/>evidence state"]
    intelligence["intelligence<br/>scores, scenarios, explanations"]
    lab["lab<br/>plans and outcomes"]
    runtime["runtime<br/>execution"]

    foundation --> intelligence
    core --> intelligence
    knowledge --> intelligence
    intelligence --> lab
    intelligence --> runtime
```

## What Makes This Package Different

- it does not claim to be raw truth
- it turns evidence plus constraints into choices
- it must explain itself because recommendation without explanation is only
  opaque force

## What It Owns

- candidate scoring and ranking policy
- scenario evaluation and recommendation logic
- explanation and reporting surfaces for those decisions

## Why This Package Matters More Now

- the repository now has enough benchmark, runtime, and grounding depth that
  recommendation posture can no longer hide behind generic prose
- stronger workflow families create stronger overconfidence risk, which this
  package must expose rather than smooth away
- lab consequence now depends on explicit analytical judgment instead of an
  implied handoff

## Shared Reader Routes

- Use [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
  when the question is still about grounding, recommendation posture, or public
  artifact roles rather than one intelligence-owner module.
- Use [Workflow Consequence Maps](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-consequence-maps/)
  when the question is whether current recommendation language already outruns
  the weakest downstream boundary.
- Use [What Changed The Recommendation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-changed-the-recommendation/)
  when the question is which contradiction, comparator, or lab burden actually
  moved the recommendation.
- Use [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
  when the family trust sentence is still the main question.

## Start Inside This Package

- Open [Foundation](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/)
  for the package role and boundary.
- Open [Architecture](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/)
  when the question is how scoring, scenarios, and explanations are arranged.
- Open [Interfaces](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/)
  when the issue is a policy-facing surface or explanation output.

## What It Refuses

- evidence truth and contradiction handling
- durable program contracts and shared payload meaning
- execution and operator-facing runtime behavior

## Strongest Proof Route

- start at [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
  when the question is still repository-wide
- continue to [Foundation](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/)
  for package-owned recommendation surfaces
- open the workflow confidence and challenge handbooks once the question is no
  longer about trust language and is clearly about analytical judgment

## First Proof Check

- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- `packages/bijux-proteomics-intelligence/tests`
- explainability and reporting modules once a claim narrows to one surface
