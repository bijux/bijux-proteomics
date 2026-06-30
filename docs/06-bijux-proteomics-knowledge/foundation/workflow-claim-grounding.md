---
title: Workflow Claim Grounding
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-01
---

# Workflow Claim Grounding

`bijux-proteomics-knowledge` now ships one sentence-grounding surface per
workflow family.

The point is simple:
public trust language should be inspectable sentence by sentence rather than
treated as a block of prose that happens to sound careful.

## Why This Surface Matters

- this is where the repository proves that public trust language is anchored to
  named evidence owners instead of stylistic restraint
- sentence grounding is now one of the clearest signs that the repository has
  matured beyond benchmark packets into reviewable scientific explanation
- when this page is weak, every stronger release sentence above it becomes
  easier to overstate

## What Ships

- one workflow-family claim citation table built by `get_workflow_claim_citation_table(...)`
- one workflow-family unsupported-claim ledger built by
  `get_workflow_unsupported_claim_ledger(...)`
- one workflow-family contradiction triage report built by
  `get_workflow_contradiction_triage_report(...)`

## What These Surfaces Cover

- the claim-bearing sentences in each flagship trust page
- the claim-bearing narrative fields in each outsider packet
- the currently shipped sentences whose wording is still thinner than the
  public proof

These surfaces intentionally do **not** treat section headers, artifact-link
labels, or raw citation digest lines as scientific claims.

## How To Read The Grounding Pack

- read the claim citation table when the question is which sentence has direct
  named support
- read the unsupported-claim ledger when the wording sounds smoother than the
  actual proof
- read the contradiction triage report when a sentence is supported and still
  scientifically narrowed by conflicting evidence

## Workflow IDs

- `dda`: `outsider_review:dda`, `unsupported_claim_ledger:dda`
- `dia`: `outsider_review:dia`, `unsupported_claim_ledger:dia`
- `lfq`: `outsider_review:lfq`, `unsupported_claim_ledger:lfq`
- `ptm`: `outsider_review:ptm`, `unsupported_claim_ledger:ptm`
- `targeted`: `outsider_review:targeted`, `unsupported_claim_ledger:targeted`
- `multiplex`: `unsupported_claim_ledger:multiplex`

## Why This Belongs Here

This package already owns evidence state, contradiction handling, and
workflow-family scientific reading packs.

Sentence grounding belongs in the same owner because it is still evidence truth
work:
the job is to show exactly what public wording is supported, what is merely
bounded, and what still needs stronger proof.

## What This Still Does Not Do

- it does not decide recommendation posture by itself
- it does not hide contradiction just because a sentence has some support
- it does not replace runtime, lab, or benchmark review surfaces that test the
  same sentence under execution or consequence pressure

## Combined Consequence Route

This page names the scientific sentence support.

Open [Workflow Consequence Maps](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-consequence-maps/)
when the next question is how contradiction pressure changes the allowed
recommendation and assay posture instead of just the sentence itself.
