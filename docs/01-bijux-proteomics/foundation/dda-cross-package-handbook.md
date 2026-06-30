---
title: DDA Cross-Package Handbook
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-09
---

# DDA Cross-Package Handbook

This page follows one real flagship DDA path across all six product packages so
the reader does not need to open seven separate handbooks before they can see
how the repository actually cooperates.

## One Benchmark Path

| owner | question this owner answers on the DDA path | best evidence surface |
| --- | --- | --- |
| `bijux-proteomics-foundation` | Which identifiers, JSON envelopes, and deterministic hashes keep the DDA evidence chain stable across packages? | [bijux-proteomics-foundation Foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/) |
| `bijux-proteomics-core` | Which copied benchmark package, acceptance bars, and workflow contracts define the DDA scientific lane? | [DDA Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dda-benchmark-lineage/) and [Flagship Acceptance Bars](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-acceptance-bars/) |
| `bijux-proteomics-runtime` | Which DDA execution lane is actually supported today, and what does the current rerun limit still block? | [Black-Box Benchmark Dashboard](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/black-box-benchmark-dashboard/) and [Runtime Execution Boundary](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-execution-boundary/) |
| `bijux-proteomics-knowledge` | Which references, comparators, and contradictions still ground the DDA sentence? | [Workflow Claim Grounding](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-claim-grounding/) and [Workflow Literature Audits](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-literature-audits/) |
| `bijux-proteomics-intelligence` | Which recommendation pressure, downgrade logic, and outsider challenge surfaces keep DDA language bounded? | [Workflow Recommendation Confidence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/workflow-recommendation-confidence/) and [Workflow Recommendation Challenges](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/workflow-recommendation-challenges/) |
| `bijux-proteomics-lab` | Which assay burden and follow-up consequence still cap the DDA story downstream? | [Workflow Consequence Maps](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-consequence-maps/) and [Outcome Learning Loops](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/outcome-learning-loops/) |

## Why DDA Stops Where It Stops

- The current DDA run mode is `import_only`, so runtime truth still depends on
  imported external-engine output rather than an in-repository raw search lane.
- Core still owns the benchmark lineage and acceptance language, which keeps
  DDA from sounding broader than the current package and challenge evidence.
- Knowledge and intelligence keep the DDA sentence honest by carrying
  comparator pressure, reference support, and downgrade triggers.
- Lab consequence remains narrower than a fully raw-executable family because
  the assay burden and downstream support still depend on imported search truth.

## Next Routes

- Open [Why Trust DDA](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-dda/)
  for the release-facing sentence and blocker list.
- Open [Scientist Journey](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/scientist-journey/)
  when the question is the general reader route rather than DDA specifically.
- Open [Repository Shape Rationale](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/repository-shape-rationale/)
  when the question becomes why these owners stay separate at all.
