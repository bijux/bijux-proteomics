---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-04
---

# Public Imports

The public Python surface of `bijux-proteomics-intelligence` starts at the package import root and any
intentionally exported modules beneath it.

This page keeps import visibility honest. Not every importable symbol is public,
and not every public symbol should be left implicit. Readers should be able to
tell what the package is prepared to support as a Python-facing boundary.

Treat the interfaces pages for `bijux-proteomics-intelligence` as the bridge between implementation detail and caller expectation. They should show what the package is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    page["Public Imports<br/>clarifies: identify contracts | see caller impact | review compatibility"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    surface1["HTTP app in src/bijux_proteomics_intelligence/api/v1"]
    surface1 --> page
    surface2["schema files in api/bijux-proteomics-intelligence/v1"]
    surface2 --> page
    surface3["CLI entrypoint in src/bijux_proteomics_intelligence/interfaces/cli/entrypoint.py"]
    surface3 --> page
    proof1["execution store records"]
    page --> proof1
    proof2["api/bijux-proteomics-intelligence/v1/schema.yaml"]
    page --> proof2
    proof3["api/bijux-proteomics-intelligence/v1/schema.hash"]
    page --> proof3
    review1["tests/regression and tests/smoke for replay and storage protection"]
    review1 -.raises compatibility pressure on.-> page
    review2["tests/unit for api, contracts, core, interfaces, model, and runtime"]
    review2 -.raises compatibility pressure on.-> page
    review3["tests/e2e for governed flow behavior"]
    review3 -.raises compatibility pressure on.-> page
    class page page;
    class surface1,surface2,surface3 positive;
    class proof1,proof2,proof3 anchor;
    class review1,review2,review3 caution;
```

## Import Anchor

- import root: `bijux_proteomics_intelligence`
- package source root: `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`

## Concrete Anchors

- CLI entrypoint in src/bijux_proteomics_intelligence/interfaces/cli/entrypoint.py
- HTTP app in src/bijux_proteomics_intelligence/api/v1
- schema files in api/bijux-proteomics-intelligence/v1
- api/bijux-proteomics-intelligence/v1/schema.yaml

## Use This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Public Imports` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What This Page Answers

- which public or operator-facing surfaces `bijux-proteomics-intelligence` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Reviewer Lens

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Honesty Boundary

This page can identify the intended public surfaces of `bijux-proteomics-intelligence`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Next Checks

- move to operations when the caller-facing question becomes procedural or environmental
- move to quality when compatibility or evidence of protection becomes the real issue
- move back to architecture when a public-surface question reveals a deeper structural drift

## Purpose

This page keeps the import-facing contract visible when refactoring package internals.

## Stability

Keep it aligned with the actual package source tree and documented import paths.
