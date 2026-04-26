---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Public Imports

The public Python surface of `bijux-proteomics-core` starts at the package import root and any
intentionally exported modules beneath it.

This page keeps import visibility honest. Not every importable symbol is public,
and not every public symbol should be left implicit. Readers should be able to
tell what the package is prepared to support as a Python-facing boundary.

Treat the interfaces pages for `bijux-proteomics-core` as the bridge between implementation detail and caller expectation. They should show what the package is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    surf1["program APIs"]
    surf2["configuration surfaces"]
    surf3["contract artifacts"]
    page["bijux-proteomics-core<br/>public imports"]
    caller1["runtime implementers"]
    caller2["policy reviewers"]
    caller3["workflow authors"]
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

## Import Anchor

- import root: `bijux_proteomics`
- package source root: `packages/bijux-proteomics-core/src/bijux_proteomics`

## Concrete Anchors

- CLI entrypoint in src/bijux_proteomics/interfaces/cli.py
- HTTP app in src/bijux_proteomics/programs.py
- program schemas in src/bijux_proteomics/programs.py
- src/bijux_proteomics/programs.py

## Use This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Public Imports` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What This Page Answers

- which public or operator-facing surfaces `bijux-proteomics-core` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Reviewer Lens

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Honesty Boundary

This page can identify the intended public surfaces of `bijux-proteomics-core`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Next Checks

- move to operations when the caller-facing question becomes procedural or environmental
- move to quality when compatibility or evidence of protection becomes the real issue
- move back to architecture when a public-surface question reveals a deeper structural drift

## Purpose

This page keeps the import-facing contract visible when refactoring package internals.

## Stability

Keep it aligned with the actual package source tree and documented import paths.
