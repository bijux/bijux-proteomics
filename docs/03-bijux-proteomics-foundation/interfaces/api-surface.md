---
title: API Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# API Surface

HTTP-facing behavior should be discoverable from tracked schema files and the
owning API modules.

This page shows which API assets matter, where they live, and why a caller can treat them as stable enough to depend on before reading code.

The interface pages define what `bijux-proteomics-foundation` is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    surf1["public imports"]
    surf2["data contracts"]
    surf3["artifact compatibility"]
    page["bijux-proteomics-foundation<br/>API surface"]
    caller1["downstream packages"]
    caller2["schema reviewers"]
    caller3["migration maintainers"]
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

## API Artifacts

- src/bijux_proteomics_foundation/schema.py
- src/bijux_proteomics_foundation/schema.py

## Boundary Modules

- CLI entrypoint in src/bijux_proteomics_foundation/__init__.py
- HTTP app in src/bijux_proteomics_foundation/schema.py
- schema contracts in src/bijux_proteomics_foundation/schema.py

## Concrete Anchors

- CLI entrypoint in src/bijux_proteomics_foundation/__init__.py
- HTTP app in src/bijux_proteomics_foundation/schema.py
- schema contracts in src/bijux_proteomics_foundation/schema.py
- src/bijux_proteomics_foundation/schema.py

## Open This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `API Surface` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What You Can Resolve Here

- which public or operator-facing surfaces `bijux-proteomics-foundation` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Review Focus

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Limits

This page can identify the intended public surfaces of `bijux-proteomics-foundation`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Read Next

- open operations when the caller-facing question becomes procedural or environmental
- open quality when compatibility or evidence of protection becomes the real issue
- open architecture when a public-surface question reveals a deeper structural drift

