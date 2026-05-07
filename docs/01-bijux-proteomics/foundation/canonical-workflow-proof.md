---
title: Canonical Workflow Proof
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Canonical Workflow Proof

`bijux-proteomics` now has one checked canonical workflow family:
`reviewable-proteomics`.

That phrase is intentionally narrow. It means one governed workflow proof set
exists from sequence intake through search/confidence, quantification, PTM
review, scientific-kernel review, evidence review, decision review, lab
handoff, and follow-up. It does **not** mean the repository now has broad
proteomics workflow coverage.

## Claim Taxonomy

Workflow-facing claims in this repository should stay in one of four tiers:

- `owned_contract`
- `benchmark_backed_behavior`
- `runtime_proven_workflow`
- `future_work`

The canonical workflow proof set is the place where `runtime_proven_workflow`
claims are allowed. If a workflow family does not have a checked proof set with
artifact paths and validating tests, it should stay in `benchmark_backed_behavior`
or `future_work`.

## What Exists Now

The current canonical proof set proves one narrow workflow story:

- runtime-owned sequence, search/confidence, quantification, PTM, and lab
  handoff artifacts
- core-owned scientific-kernel review with explicit untrustworthy-result
  checklists
- knowledge-owned evidence review packet
- intelligence-owned decision review with downgrade chains
- lab-owned follow-up packet with explicit progression blockers

## What This Does Not Mean

The canonical proof set does not authorize broad claims about:

- glycopeptide workflow coverage
- library-search scientific depth
- external-engine parity as solved scientific behavior

Those remain explicit boundary-only surfaces until they have their own checked
proof sets.

## Reference-Grade Boundary

One undeniable workflow is necessary, but it is not enough by itself to make
the whole repository `reference-grade` or `elite`.

Those stronger postures stay blocked until repository-level release truth is
clean on four fronts at the same time:

- the canonical workflow manifest stays valid and shortcut-free
- ranking behavior proves itself on a governed decision-quality corpus
- generated governance reports are fresh before release
- reopened completion pressure and architectural-ready package gaps no longer
  contradict stronger maturity claims

## Boundary

Only `reviewable-proteomics` may be described with canonical workflow prose.
Every other workflow family remains future-only until it has its own
artifact-backed proof surface.
