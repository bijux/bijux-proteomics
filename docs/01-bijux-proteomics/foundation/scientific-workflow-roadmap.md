---
title: Scientific Workflow Roadmap
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-27
---

# Scientific Workflow Roadmap

`bijux-proteomics` already has substantial package contracts. What it does not
yet have is the full scientific workflow spine those contracts should serve.

## Current State

Today the repository is strongest in these areas:

- package boundaries are explicit and reviewable
- program, evidence, ranking, and assay-planning models are typed and reusable
- runtime, compatibility, and governance surfaces are already checked and
  release-aware

## Next State

The next durable step is to make one proteomics workflow legible end to end:

- sequence and program intake
- evidence review and evidence-gap detection
- assay planning and execution ordering
- decision review and advancement
- learning-loop feedback into the next revision

That workflow should remain reviewable from repository contracts rather than
being hidden inside one runtime path or one notebook.

## Why This Matters

Without an explicit roadmap, the repository can look deeper than it is. The
goal is not to decorate package boundaries with ambition. The goal is to grow a
real scientific workflow on top of those boundaries without losing ownership
clarity.

The roadmap is about what should exist next. The exact list of what does not
yet exist lives in
[Current Capability Limits](./current-capability-limits.md).

## Boundary

This roadmap should keep the repository honest. If a future claim sounds like a
workflow capability, it should land either as one concrete workflow contract or
stay here as future work until it exists.
