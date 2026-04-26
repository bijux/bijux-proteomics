---
title: Compatibility Commitments
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Compatibility Commitments

Compatibility in `bijux-proteomics-knowledge` should be explicit: stable commands, tracked schemas,
durable artifacts, and release notes that explain intentional breakage.

This page gives readers a realistic sense of the compatibility bar.
It is more valuable to be clear about what triggers review than to sound
generously stable while leaving the real boundary ambiguous.

These interface pages show what `bijux-proteomics-knowledge` is prepared to
defend before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    contract1["claim state"]
    contract2["trust summaries"]
    contract3["contradiction handling"]
    page["bijux-proteomics-knowledge<br/>compatibility commitments"]
    proof1["package code"]
    proof2["tests"]
    proof3["tracked artifacts"]
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

## Compatibility Anchors

- README.md
- CHANGELOG.md
- pyproject.toml

## Review Rule

Breaking changes must be visible in code, docs, and validation together.

## Concrete Anchors

- CLI entrypoint in src/bijux_proteomics_knowledge/evidence.py
- HTTP app in src/bijux_proteomics_knowledge/claims.py
- knowledge contracts in src/bijux_proteomics_knowledge/schema.py
- src/bijux_proteomics_knowledge/schema.py

## Open This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `Compatibility Commitments` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What You Can Resolve Here

- which public or operator-facing surfaces `bijux-proteomics-knowledge` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Review Focus

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Limits

This page can identify the intended public surfaces of `bijux-proteomics-knowledge`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Read Next

- open operations when the caller-facing question becomes procedural or environmental
- open quality when compatibility or evidence of protection becomes the real issue
- move back to architecture when a public-surface question reveals a deeper structural drift

