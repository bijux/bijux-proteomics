---
title: bijux-proteomics-knowledge
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-01
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
- grounding, literature-pressure, and biological-context surfaces that stop the
  repository from sounding more certain than its evidence state earns

## Why This Package Matters More Now

- public trust language is now challenged by explicit grounding routes instead
  of general scientific tone
- stronger workflow packets need stronger contradiction and citation discipline
- downstream recommendation and lab consequence can now be traced back to
  visible evidence state instead of inferred background knowledge
- biological reasoning is now explicit enough that readers can inspect where
  confidence came from, where contradiction remains open, and why hesitation is
  scientifically responsible instead of operationally inconvenient

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

## Reader Questions This Package Can Answer

- which parts of a workflow story are directly grounded and which still depend
  on bounded inference
- where contradiction remains unresolved instead of being smoothed into a
  single recommendation sentence
- how literature pressure, comparator pressure, and biological-context pressure
  reshape confidence before a lab or decision surface is allowed to promote the
  claim
- whether a public workflow sentence has earned trust through explicit evidence
  state rather than tone

## Evidence Proof Surfaces

- decision-support pages when the question is still cross-package and public
  facing
- workflow grounding and literature audit pages when the real issue is whether
  the repository can justify what it says
- architecture pages for claim, contradiction, and confidence separation
- interfaces pages for evidence and claim-facing contracts that downstream
  packages must not rewrite

## What It Refuses

- scoring and recommendation policy
- execution orchestration and operator surfaces
- assay planning and outcome promotion

## Why Readers Underestimate Knowledge

- this package is easy to mistake for a passive ledger unless the contradiction
  and grounding routes are shown clearly
- repository honesty depends on this owner more than on any confidence-sounding
  prose elsewhere
- stronger scientific depth only becomes visible to a reader when evidence
  state, hesitation, and literature pressure are documented as first-class
  surfaces

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
- grounding, citation, and contradiction-review artifacts when the public claim
  itself is under scrutiny
