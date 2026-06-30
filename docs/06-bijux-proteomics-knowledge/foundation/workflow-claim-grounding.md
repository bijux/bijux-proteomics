---
title: Workflow Claim Grounding
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-05-08
---

# Workflow Claim Grounding

`bijux-proteomics-knowledge` now ships one sentence-grounding surface per
workflow family.

The point is simple:
public trust language should be inspectable sentence by sentence rather than
treated as a block of prose that happens to sound careful.

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

## Combined Consequence Route

This page names the scientific sentence support.

Open [Workflow Consequence Maps](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-consequence-maps/)
when the next question is how contradiction pressure changes the allowed
recommendation and assay posture instead of just the sentence itself.
