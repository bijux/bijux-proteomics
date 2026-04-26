---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-04
---

# CLI Surface

The CLI surface is the operator-facing command layer for `agentic-proteins`. It
should tell a reader which commands are deliberate entrypoints and which ones
are just local implementation detail.

Command surfaces tend to become contracts early, because people script them,
share them in tickets, and paste them into automation. This page should make
that contract status visible instead of accidental.

Treat the interfaces pages for `agentic-proteins` as the bridge between implementation detail and caller expectation. They should show what the package is prepared to defend before a dependency forms.

## Visual Summary

```mermaid
flowchart LR
    page["CLI Surface<br/>clarifies: identify contracts | see caller impact | review compatibility"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    surface1["HTTP app in src/agentic_proteins/api/v1"]
    surface1 --> page
    surface2["canonical API schema in apis/bijux-proteomics-runtime/v1 with compatibility mirror in apis/agentic-proteins/v1"]
    surface2 --> page
    surface3["CLI entrypoint in src/agentic_proteins/interfaces/cli.py"]
    surface3 --> page
    proof1["apis/bijux-proteomics-runtime/v1/schema.yaml (canonical) and apis/agentic-proteins/v1/schema.yaml (compatibility mirror)"]
    page --> proof1
    proof2["apis/bijux-proteomics-runtime/v1/schema.yaml (canonical) and apis/agentic-proteins/v1/schema.yaml (compatibility mirror)"]
    page --> proof2
    proof3["execution store records"]
    page --> proof3
    review1["tests/unit for api, contracts, core, interfaces, model, and runtime"]
    review1 -.raises compatibility pressure on.-> page
    review2["tests/e2e for governed flow behavior"]
    review2 -.raises compatibility pressure on.-> page
    review3["tests/regression and tests/smoke for replay and storage protection"]
    review3 -.raises compatibility pressure on.-> page
    class page page;
    class surface1,surface2,surface3 positive;
    class proof1,proof2,proof3 anchor;
    class review1,review2,review3 caution;
```

## Command Facts

- canonical command: `agentic-proteins`
- interface modules: CLI entrypoint in src/agentic_proteins/interfaces/cli.py, HTTP app in src/agentic_proteins/api/v1, canonical API schema in apis/bijux-proteomics-runtime/v1 with compatibility mirror in apis/agentic-proteins/v1

## Concrete Anchors

- CLI entrypoint in src/agentic_proteins/interfaces/cli.py
- HTTP app in src/agentic_proteins/api/v1
- canonical API schema in apis/bijux-proteomics-runtime/v1 with compatibility mirror in apis/agentic-proteins/v1
- apis/bijux-proteomics-runtime/v1/schema.yaml (canonical) and apis/agentic-proteins/v1/schema.yaml (compatibility mirror)

## Use This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Use `CLI Surface` to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

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

- move to operations when the caller-facing question becomes procedural or environmental
- move to quality when compatibility or evidence of protection becomes the real issue
- move back to architecture when a public-surface question reveals a deeper structural drift

## Purpose

This page points maintainers toward the command entrypoints and their owning code.

## Stability

Keep it aligned with the declared scripts and the interface modules that implement them.
