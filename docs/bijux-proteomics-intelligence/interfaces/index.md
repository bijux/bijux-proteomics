---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-04
---

# Interfaces

This section explains which commands, APIs, imports, schemas, and artifacts `bijux-proteomics-intelligence` is prepared to stand behind as real surfaces.

These pages explain the public face of `bijux-proteomics-intelligence`. They help a caller separate deliberate contracts from incidental visibility before a dependency hardens around the wrong surface.

Treat the interfaces pages for `bijux-proteomics-intelligence` as the bridge between implementation detail and caller expectation. They should show what the package is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    page["Interfaces<br/>clarifies: identify contracts | see caller impact | review compatibility"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    surface1["HTTP app in src/bijux_proteomics_intelligence/evaluators.py"]
    surface1 --> page
    surface2["ranking contracts in src/bijux_proteomics_intelligence/policies.py"]
    surface2 --> page
    surface3["CLI entrypoint in src/bijux_proteomics_intelligence/briefs.py"]
    surface3 --> page
    proof1["src/bijux_proteomics_intelligence/policies.py"]
    page --> proof1
    proof2["src/bijux_proteomics_intelligence/policies.py"]
    page --> proof2
    proof3["execution store records"]
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

## Pages in This Section

- [CLI Surface](cli-surface.md)
- [API Surface](api-surface.md)
- [Configuration Surface](configuration-surface.md)
- [Data Contracts](data-contracts.md)
- [Artifact Contracts](artifact-contracts.md)
- [Entrypoints and Examples](entrypoints-and-examples.md)
- [Operator Workflows](operator-workflows.md)
- [Public Imports](public-imports.md)
- [Compatibility Commitments](compatibility-commitments.md)

## Read Across the Package

- [Foundation](../foundation/index.md) when you need the package boundary and ownership story first
- [Architecture](../architecture/index.md) when the question becomes structural, modular, or execution-oriented
- [Operations](../operations/index.md) when the question becomes procedural, environmental, diagnostic, or release-oriented
- [Quality](../quality/index.md) when the question becomes proof, risk, trust, or review sufficiency

## Concrete Anchors

- CLI entrypoint in src/bijux_proteomics_intelligence/briefs.py
- HTTP app in src/bijux_proteomics_intelligence/evaluators.py
- ranking contracts in src/bijux_proteomics_intelligence/policies.py
- src/bijux_proteomics_intelligence/policies.py

## Use This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Interfaces` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

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

This page explains how to use the interfaces section for `bijux-proteomics-intelligence` without repeating the detail that belongs on the topic pages beneath it.

## Stability

This page is part of the canonical package docs spine. Keep it aligned with the current package boundary and the topic pages in this section.
