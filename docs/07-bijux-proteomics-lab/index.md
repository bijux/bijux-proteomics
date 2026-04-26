---
title: bijux-proteomics-lab
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-lab

`bijux-proteomics-lab` owns lab-facing execution in `bijux-proteomics`. It
turns plans and decisions into assay work, captures outcomes, and keeps
experiment-facing state separate from lower-layer contracts and runtime control.

## What It Owns

- assay planning and experiment-facing workflows
- outcome capture, promotion, and closed-loop lab decisions
- lab-facing artifacts that connect recommendations to real execution

## What It Refuses

- evidence truth that belongs in knowledge
- recommendation policy that belongs in intelligence
- general execution orchestration that belongs in runtime

## Start With

- Open [Foundation](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/)
  for the package role and boundary.
- Open [Interfaces](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/)
  when the question is a lab-facing contract or artifact surface.
- Open [bijux-proteomics-runtime](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
  when the issue becomes general execution control rather than lab ownership.

## First Proof Check

- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab`
- `packages/bijux-proteomics-lab/tests`
- outcome and planning modules once a claim narrows to one surface
