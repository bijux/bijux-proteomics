---
title: Compatibility Commitments
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-04
---

# Compatibility Commitments

Compatibility in `bijux-proteomics-foundation` should be explicit: stable commands, tracked schemas,
durable artifacts, and release notes that explain intentional breakage.

This page should leave readers with a realistic sense of the compatibility bar.
It is more valuable to be clear about what triggers review than to sound
generously stable while leaving the real boundary ambiguous.

Treat the interfaces pages for `bijux-proteomics-foundation` as the bridge between implementation detail and caller expectation. They should show what the package is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart TB
    page["Compatibility Commitments<br/>clarifies: identify contracts | see caller impact | review compatibility"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    surface1["CLI entrypoint in src/bijux_proteomics_foundation/__init__.py"]
    surface1 --> page
    surface2["HTTP app in src/bijux_proteomics_foundation/schema.py"]
    surface2 --> page
    surface3["schema contracts in src/bijux_proteomics_foundation/schema.py"]
    surface3 --> page
    proof1["src/bijux_proteomics_foundation/schema.py"]
    page --> proof1
    proof2["execution store records"]
    page --> proof2
    proof3["src/bijux_proteomics_foundation/schema.py"]
    page --> proof3
    review1["tests/e2e for governed flow behavior"]
    review1 -.raises compatibility pressure on.-> page
    review2["tests/regression and tests/smoke for replay and storage protection"]
    review2 -.raises compatibility pressure on.-> page
    review3["tests/unit for api, contracts, core, interfaces, model, and runtime"]
    review3 -.raises compatibility pressure on.-> page
    class page page;
    class surface1,surface2,surface3 positive;
    class proof1,proof2,proof3 anchor;
    class review1,review2,review3 caution;
```

## Compatibility Anchors

- README.md
- CHANGELOG.md
- pyproject.toml

## Review Rule

Breaking changes must be visible in code, docs, and validation together.

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

Use `Compatibility Commitments` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

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

This page describes what should trigger compatibility review for the package.

## Stability

Keep it aligned with the package's actual public surfaces and release process.
