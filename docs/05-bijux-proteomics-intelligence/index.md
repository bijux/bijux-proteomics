---
title: bijux-proteomics-intelligence
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-intelligence

`bijux-proteomics-intelligence` owns decision policy in
`bijux-proteomics`. It turns evidence and program constraints into scores,
rankings, scenarios, and explanations that remain inspectable instead of
pretending to be upstream fact. This is where the system stops only describing
the world and starts making judgments about what should happen next.

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

## Start With

- Open [Foundation](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/)
  for the package role and boundary.
- Open [Interfaces](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/)
  when the issue is a policy-facing surface or explanation output.
- Open [bijux-proteomics-knowledge](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
  when the disagreement is about evidence state rather than recommendation
  policy.

## What It Refuses

- evidence truth and contradiction handling
- durable program contracts and shared payload meaning
- execution and operator-facing runtime behavior

## First Proof Check

- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- `packages/bijux-proteomics-intelligence/tests`
- explainability and reporting modules once a claim narrows to one surface
