---
title: Local Development
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Local Development

Local work should begin in the owning package and escalate to root automation
only when the change genuinely crosses package, schema, or repository
boundaries.

```mermaid
flowchart LR
    change["need to make a change"]
    local["owning package"]
    root["root automation<br/>for cross-package work"]
    proof["docs, schemas, and tests update together"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    change --> local
    change --> root
    local --> proof
    root --> proof
    class proof page;
    class local,root anchor;
    class change action;
```

## Working Rules

- make package-local changes in the owning package directory
- use root automation when the change spans packages, schemas, or shared docs
- keep documentation updates reviewable alongside the code that changes
  behavior

## Shared Inputs

- `pyproject.toml` for workspace metadata and commit conventions
- `tox.ini` for root validation environments
- `Makefile` and `makes/` for common workflows

