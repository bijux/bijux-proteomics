---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Common Workflows

Most work on `bijux-proteomics-knowledge` follows a small set of repeatable
library-maintenance paths.

## Visual Summary

```mermaid
flowchart LR
    step1["review evidence inputs"]
    step2["inspect claim state"]
    step3["validate trust outputs"]
    page["bijux-proteomics-knowledge<br/>common workflows"]
    op1["scientific reviewers"]
    op2["runtime readers"]
    op3["release maintainers"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    step1 --> page
    step2 --> page
    step3 --> page
    page --> op1
    page --> op2
    page --> op3
    class page page;
    class step1,step2,step3 positive;
    class op1,op2,op3 anchor;
```

## Recurring Paths

1. Add or adjust evidence and claim behavior:
`adapters.py` -> `evidence.py` -> `claims.py` -> tests.
2. Change conflict policy logic:
`resolution.py` -> `review.py` -> tests.
3. Change serialization or schema compatibility:
`schema.py`/`serialization.py` -> tests -> docs/changelog.

## Code Areas

- `src/bijux_proteomics_knowledge/evidence.py` for evidence records and trust scoring
- `src/bijux_proteomics_knowledge/claims.py` for claim state and lineage
- `src/bijux_proteomics_knowledge/resolution.py` for conflict resolution policy
- `src/bijux_proteomics_knowledge/review.py` for decision-facing summaries
- `src/bijux_proteomics_knowledge/graph.py` for graph validation and trace paths

## Concrete Anchors

- `packages/bijux-proteomics-knowledge/pyproject.toml` for package metadata
- `packages/bijux-proteomics-knowledge/README.md` for local package framing
- `packages/bijux-proteomics-knowledge/tests` for executable operational backstops

## Open This Page When

- you are installing, running, diagnosing, or releasing the package
- you need repeatable operational anchors rather than architectural framing
- you are responding to package behavior in local work, CI, or incident pressure

## Decision Rule

Use `Common Workflows` to decide whether a maintainer can repeat the package workflow from checked-in assets instead of memory. If a step works only because someone already knows the trick, the workflow is not documented clearly enough yet.

## What This Page Answers

- how `bijux-proteomics-knowledge` is installed, run, diagnosed, and released in practice
- which checked-in files and tests anchor the operational story
- where a maintainer should look first when the package behaves differently

## Reviewer Lens

- verify that setup, workflow, and release statements still match package metadata and current commands
- check that operational guidance still points at real diagnostics and validation paths
- confirm that maintainer advice still works under current local and CI expectations

## Honesty Boundary

This page shows how `bijux-proteomics-knowledge` is operated today, but the checked-in commands, artifacts, and validation remain the source of truth. Use those assets to confirm the workflow in a real environment.

## Next Checks

- open interfaces when the operational path depends on a specific surface contract
- open quality when the question becomes whether the workflow is sufficiently proven
- move back to architecture when operational complexity suggests a structural problem

