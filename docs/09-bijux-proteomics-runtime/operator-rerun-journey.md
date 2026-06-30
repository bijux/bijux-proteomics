---
title: Operator Rerun Journey
audience: operator
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-05-09
---

# Operator Rerun Journey

Start here when the question is: I want to run or replay one flagship workflow
family and I do not want to guess which evidence or runtime surface matters
next.

## One-Hop Route

| question | owner | best page |
| --- | --- | --- |
| Which family am I reopening and what language does it currently earn? | repository docs | [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/) |
| Which public benchmark package and companion package do I need first? | `bijux-proteomics-core` | [Benchmark Rerun Kits](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/benchmark-rerun-kits/) |
| Which software and dependency combinations are actually supported? | `bijux-proteomics-runtime` | [Runtime Environment Contracts](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-environment-contracts/) |
| What run mode and rerun blockers apply right now? | `bijux-proteomics-runtime` | [Black-Box Benchmark Dashboard](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/black-box-benchmark-dashboard/) |
| Which exact replay or invalidation challenge should I run? | `bijux-proteomics-runtime` | [Runtime Replay Challenges](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-replay-challenges/) |
| Which artifacts must appear and what stability class do they owe? | `bijux-proteomics-runtime` | [Black-Box Run Verification](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/black-box-run-verification/) and [Runtime Artifact Stability](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-artifact-stability/) |
| Which failure boundaries still block stronger language? | repository docs | [What Would Make This Repository Ready](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-would-make-this-repository-ready/) |
| Which acceptance bars must the rerun clear before a maintainer widens wording? | `bijux-proteomics-core` | [Flagship Acceptance Bars](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-acceptance-bars/) |

## Minimal Operator Checklist

1. Confirm the workflow family sentence and current blocker set in
   [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/).
2. Open the matching rerun kit and benchmark lineage pages before touching the
   runtime handbook.
3. Verify the supported environment and run mode before rerunning a command.
4. Use the replay challenge and run verification surfaces as the acceptance
   contract, not maintainer prose.
5. Stop at the published refusal or blocker surface instead of improvising a
   stronger claim when the rerun lane degrades.

## Boundary

This route should get an operator from public package to checked rerun evidence
without a detour through package architecture prose.
