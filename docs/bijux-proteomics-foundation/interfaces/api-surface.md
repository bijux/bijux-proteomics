---
title: API Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-04
---

# API Surface

HTTP-facing behavior should be discoverable from tracked schema files and the
owning API modules.

The goal of this page is clarity before code-reading. A reviewer should be able
to see which API assets matter, where they live, and why a caller would treat
them as stable enough to depend on.

Treat the interfaces pages for `bijux-proteomics-foundation` as the bridge between implementation detail and caller expectation. They should show what the package is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    callers["callers"] --> api["API surface"]
    api --> validate["validate inputs"]
    validate --> models["canonical models"]
    models --> ser["serialize / deserialize"]
    ser --> outputs["stable outputs"]
    api -.hides.-> internals["internal helpers"]
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

## Use This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `API Surface` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

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

This page ties API behavior to tracked code and schema assets.

## Stability

Keep it aligned with the actual API modules and schema files.
