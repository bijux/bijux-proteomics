---
title: Entrypoints and Examples
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Entrypoints and Examples

The fastest way to understand the package interfaces is to pair entrypoints
with concrete examples.

Examples are doing real work here. They let an impatient reader test whether the
package story is credible without reconstructing usage from source alone.

These interface pages show what `bijux-proteomics-lab` is prepared to defend
before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    surf1["planning APIs"]
    surf2["operator workflows"]
    surf3["assay artifacts"]
    page["bijux-proteomics-lab<br/>entrypoints and examples"]
    caller1["operators"]
    caller2["runtime orchestration"]
    caller3["reviewers of outcomes"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    surf1 --> page
    surf2 --> page
    surf3 --> page
    page --> caller1
    page --> caller2
    page --> caller3
    class page page;
    class surf1,surf2,surf3 positive;
    class caller1,caller2,caller3 anchor;
```

## Entrypoints

- CLI entrypoint in src/bijux_proteomics_lab/planning.py
- HTTP app in src/bijux_proteomics_lab/outcomes.py
- lab contracts in src/bijux_proteomics_lab/schema.py

## Example Anchors

- examples/ for minimal flows, replay violations, and datasets
- src/bijux_proteomics_lab/schema.py for schema integrity checks

## Concrete Anchors

- CLI entrypoint in src/bijux_proteomics_lab/planning.py
- HTTP app in src/bijux_proteomics_lab/outcomes.py
- lab contracts in src/bijux_proteomics_lab/schema.py
- src/bijux_proteomics_lab/schema.py

## Open This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Entrypoints and Examples` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What This Page Answers

- which public or operator-facing surfaces `bijux-proteomics-lab` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Reviewer Lens

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Honesty Boundary

This page can identify the intended public surfaces of `bijux-proteomics-lab`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Next Checks

- open operations when the caller-facing question becomes procedural or environmental
- open quality when compatibility or evidence of protection becomes the real issue
- move back to architecture when a public-surface question reveals a deeper structural drift

