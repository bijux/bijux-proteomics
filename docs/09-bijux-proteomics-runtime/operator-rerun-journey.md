---
title: Operator Rerun Journey
audience: operator
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-01
---

# Operator Rerun Journey

Use this route when the question is:
I want to reopen one flagship workflow family and I do not want to guess which
runtime proof surface matters next.

This page is intentionally narrower than the general execution overview. It is
the shortest operator-facing route from a family sentence to checked rerun
evidence.

## One-Hop Route

| question | owner | best page |
| --- | --- | --- |
| what family sentence am I reopening | repository docs | [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/) |
| which public package roots and companion package do I need first | `bijux-proteomics-runtime` with `core` assets | [Benchmark Rerun Kits](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/benchmark-rerun-kits/) |
| which environment and dependency bounds are actually supported | `bijux-proteomics-runtime` | [Runtime Environment Contracts](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-environment-contracts/) |
| what run mode and rerun boundary apply right now | `bijux-proteomics-runtime` | [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/) and [Black-Box Benchmark Dashboard](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/black-box-benchmark-dashboard/) |
| which replay or invalidation challenge should I use | `bijux-proteomics-runtime` | [Runtime Replay Challenges](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-replay-challenges/) |
| which artifacts must appear and what stability class do they owe | `bijux-proteomics-runtime` | [Black-Box Run Verification](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/black-box-run-verification/) and [Runtime Artifact Stability](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-artifact-stability/) |
| which scientific acceptance bars still cap the family even after rerun success | `bijux-proteomics-core` | [Flagship Acceptance Bars](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-acceptance-bars/) |
| where do I stop instead of inventing stronger language | repository docs | [Current Capability Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/) |

## Minimal Operator Checklist

1. confirm the family sentence and current limiter
2. open the matching primary and companion package roots
3. verify supported environment and run mode before touching the rerun lane
4. treat replay challenge and artifact verification as the acceptance contract
5. stop at the published refusal or limiter instead of turning a degraded rerun
   into a broader story

## What This Route Prevents

- guessing at which package root is canonical for a rerun
- confusing runtime reproducibility with broader scientific authority
- widening the family sentence because one local rerun happened to work
- skipping the refusal and stability surfaces when the lane degrades

## Boundary

This route should get an operator from public package root to checked rerun
evidence without requiring package-architecture reconstruction on the way.
