---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-04
---

# Data Contracts

Data contracts in `bijux-proteomics-intelligence` include schemas, structured models, and any stable
payload shape that neighboring systems are expected to understand.

This page keeps data shape changes reviewable. If a record or payload matters to
another package, another process, or a replay path, it deserves to be described
as a contract rather than left implicit in implementation details.

Treat the interfaces pages for `bijux-proteomics-intelligence` as the bridge between implementation detail and caller expectation. They should show what the package is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart RL
    page["Data Contracts<br/>clarifies: identify contracts | see caller impact | review compatibility"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    surface1["ranking contracts in src/bijux_proteomics_intelligence/policies.py"]
    surface1 --> page
    surface2["CLI entrypoint in src/bijux_proteomics_intelligence/briefs.py"]
    surface2 --> page
    surface3["HTTP app in src/bijux_proteomics_intelligence/evaluators.py"]
    surface3 --> page
    proof1["execution store records"]
    page --> proof1
    proof2["src/bijux_proteomics_intelligence/policies.py"]
    page --> proof2
    proof3["src/bijux_proteomics_intelligence/policies.py"]
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

## Contract Anchors

- src/bijux_proteomics_intelligence/policies.py
- src/bijux_proteomics_intelligence/policies.py

## Artifact Anchors

- execution store records
- replay decision artifacts
- non-determinism policy evaluations

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

Use `Data Contracts` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

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

This page explains which structured shapes deserve compatibility review.

## Stability

Keep it aligned with tracked schemas, stable models, and durable artifacts.
