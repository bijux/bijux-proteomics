---
title: bijux-proteomics-knowledge
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-06-30
---

# bijux-proteomics-knowledge

`bijux-proteomics-knowledge` owns evidence state in `bijux-proteomics`. It is
where claims, confidence, contradiction handling, and knowledge-level review
rules stay explicit instead of being spread across runtime or scoring code.
This package matters because serious systems do not only need facts; they need
structured disagreement, confidence, and traceable reasons to hesitate.

This package is also much richer now than a simple evidence ledger. It owns
selective scientific memory, contradiction-aware review, claim grounding,
literature audit routes, and biological context surfaces that stop the rest of
the product from improvising why a workflow result should be believed.

```mermaid
flowchart LR
    inputs["observations, records,<br/>derived findings"]
    claims["claims"]
    confidence["confidence"]
    contradictions["contradictions"]
    knowledge["knowledge<br/>evidence state"]
    intelligence["intelligence"]
    lab["lab"]
    runtime["runtime"]

    inputs --> claims
    inputs --> confidence
    inputs --> contradictions
    claims --> knowledge
    confidence --> knowledge
    contradictions --> knowledge
    knowledge --> intelligence
    knowledge --> lab
    knowledge --> runtime
```

## What This Package Protects

- recommendation code cannot quietly rewrite evidence state
- runtime code cannot smuggle operational convenience in as scientific truth
- contradiction is preserved as information instead of being treated as failure

## What It Owns

- evidence records and claim state
- confidence semantics and contradiction handling
- knowledge-level review boundaries used by downstream packages

## Why This Package Matters More Now

- public trust language is now challenged by explicit grounding routes instead
  of general scientific tone
- stronger workflow packets need stronger contradiction and citation discipline
- downstream recommendation and lab consequence can now be traced back to
  visible evidence state instead of inferred background knowledge

## Shared Reader Routes

- Use [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
  when the question is still about evidence, contradiction, or public belief
  posture rather than one knowledge-owner module.
- Use [Workflow Consequence Maps](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-consequence-maps/)
  when the question is how contradiction pressure should narrow the current
  recommendation before assay spend is approved.
- Use [What Changed The Recommendation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-changed-the-recommendation/)
  when the question is whether literature pressure, comparator pressure, or lab
  burden actually moved the call.
- Use [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
  when the family route is clearer than the package route.

## Start Inside This Package

- Open [Foundation](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/)
  for the package role and boundary.
- Open [Architecture](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/)
  when the concern is how claims, confidence, and contradiction handling stay
  separated.
- Open [Interfaces](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/)
  when the question is a claim, evidence, or confidence-facing contract.

## What It Refuses

- scoring and recommendation policy
- execution orchestration and operator surfaces
- assay planning and outcome promotion

## Strongest Proof Route

- start at [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
  when the question is still cross-package
- continue to [Foundation](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/)
  for package-owned evidence and grounding routes
- open the workflow grounding and literature audit pages when the real question
  is whether the current public sentence has earned its scientific backing

## First Proof Check

- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge`
- `packages/bijux-proteomics-knowledge/tests`
- confidence and contradiction modules once the claim narrows to one seam
