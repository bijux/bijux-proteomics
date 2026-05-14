---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Ownership Boundary

Lab-facing consequence belongs here instead of dissolving into ranking language
or general runtime execution.

## Keep It Here When

- the change alters assay readiness, control demands, queue or material burden,
  handoff honesty, or observed-outcome follow-through
- the best proof lives in this package's source tree and tests
- neighboring packages would otherwise overstate what downstream work is truly
  executable

## Move It Elsewhere When

- the change mainly alters scientific law, evidence truth, recommendation
  posture, or runtime execution control
- the package becomes a vague follow-up layer instead of an accountable assay
  consequence owner
- the proof surface is mostly outside downstream burden and outcome behavior
  already

## First Proof Check

- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab`
- `packages/bijux-proteomics-lab/tests`
