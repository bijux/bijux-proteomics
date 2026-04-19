---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-04
---

# Public Imports

The public Python surface of `bijux-proteomics-foundation` starts at the package import root and any
intentionally exported modules beneath it.

This page keeps import visibility honest. Not every importable symbol is public,
and not every public symbol should be left implicit. Readers should be able to
tell what the package is prepared to support as a Python-facing boundary.

Treat the interfaces pages for `bijux-proteomics-foundation` as the bridge between implementation detail and caller expectation. They should show what the package is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    callers["downstream code"] --> pub["public imports"]
    pub --> ids["identity exports"]
    pub --> models["schema model exports"]
    pub --> compat["compatibility exports"]
    pub --> ser["serialization exports"]
    pub -.shields callers from.-> private["private helpers and layout churn"]
```

## Import Anchor

- import root: `bijux_proteomics_foundation`
- package source root: `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation`

## Concrete Anchors

- CLI entrypoint in src/bijux_proteomics_foundation/__init__.py
- HTTP app in src/bijux_proteomics_foundation/schema.py
- schema contracts in src/bijux_proteomics_foundation/schema.py
- src/bijux_proteomics_foundation/schema.py

## Use This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Public Imports` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What This Page Answers

- which public or operator-facing surfaces `bijux-proteomics-foundation` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Reviewer Lens

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Honesty Boundary

This page can identify the intended public surfaces of `bijux-proteomics-foundation`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Next Checks

- move to operations when the caller-facing question becomes procedural or environmental
- move to quality when compatibility or evidence of protection becomes the real issue
- move back to architecture when a public-surface question reveals a deeper structural drift

## Purpose

This page keeps the import-facing contract visible when refactoring package internals.

## Stability

Keep it aligned with the actual package source tree and documented import paths.
