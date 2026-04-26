---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Data Contracts

Data contracts in `bijux-proteomics-intelligence` include schemas, structured models, and any stable
payload shape that neighboring systems are expected to understand.

This page keeps data shape changes reviewable. If a record or payload matters to
another package, another process, or a replay path, it deserves to be described
as a contract rather than left implicit in implementation details.

The interface pages define what `bijux-proteomics-intelligence` is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    contract1["ranking outputs"]
    contract2["policy parameters"]
    contract3["explanation expectations"]
    page["bijux-proteomics-intelligence<br/>data contracts"]
    proof1["package code"]
    proof2["tests"]
    proof3["example outputs"]
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

## Open This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Data Contracts` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What You Can Resolve Here

- which public or operator-facing surfaces `bijux-proteomics-intelligence` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Review Focus

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Limits

This page can identify the intended public surfaces of `bijux-proteomics-intelligence`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Read Next

- open operations when the caller-facing question becomes procedural or environmental
- open quality when compatibility or evidence of protection becomes the real issue
- open architecture when a public-surface question reveals a deeper structural drift

