---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Data Contracts

Data contracts in `agentic-proteins` include schemas, structured models, and any stable
payload shape that neighboring systems are expected to understand.

This page keeps data shape changes reviewable. If a record or payload matters to
another package, another process, or a replay path, it deserves to be described
as a contract rather than left implicit in implementation details.

These interface pages show what `agentic-proteins` is prepared to defend
before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    contract1["forwarding behavior"]
    contract2["import compatibility"]
    contract3["CLI preservation"]
    page["agentic-proteins<br/>data contracts"]
    proof1["package code"]
    proof2["tests"]
    proof3["runtime handoff docs"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    contract1 --> page
    contract2 --> page
    contract3 --> page
    page --> proof1
    page --> proof2
    page --> proof3
    class page page;
    class contract1,contract2,contract3 positive;
    class proof1,proof2,proof3 anchor;
```

## Contract Anchors

- apis/bijux-proteomics-runtime/v1/schema.yaml (canonical) and apis/agentic-proteins/v1/schema.yaml (compatibility mirror)
- apis/bijux-proteomics-runtime/v1/schema.yaml (canonical) and apis/agentic-proteins/v1/schema.yaml (compatibility mirror)

## Artifact Anchors

- execution store records
- replay decision artifacts
- non-determinism policy evaluations

## Concrete Anchors

- CLI entrypoint in src/agentic_proteins/interfaces/cli.py
- HTTP app in src/agentic_proteins/api/v1
- canonical API schema in apis/bijux-proteomics-runtime/v1 with compatibility mirror in apis/agentic-proteins/v1
- apis/bijux-proteomics-runtime/v1/schema.yaml (canonical) and apis/agentic-proteins/v1/schema.yaml (compatibility mirror)

## Open This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Data Contracts` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What This Page Answers

- which public or operator-facing surfaces `agentic-proteins` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Reviewer Lens

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Honesty Boundary

This page can identify the intended public surfaces of `agentic-proteins`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Next Checks

- open operations when the caller-facing question becomes procedural or environmental
- open quality when compatibility or evidence of protection becomes the real issue
- move back to architecture when a public-surface question reveals a deeper structural drift

## Purpose

This page shows which structured shapes deserve compatibility review.

## Stability

Keep it aligned with tracked schemas, stable models, and durable artifacts.
