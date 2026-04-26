---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Foundation

The foundation section explains why `bijux-proteomics` exists in this shape
before it explains how the repository is operated.

A reader should be able to leave this section with a durable understanding of
the package split, the ownership model, the shared vocabulary, and the change
rules that keep the repository legible over time.

```mermaid
flowchart LR
    topic1["platform overview"]
    topic2["scope, ownership, and layout"]
    topic3["language, docs, and change rules"]
    foundation["Repository foundation<br/>why the split exists"]
    next1["package map"]
    next2["decision rules"]
    next3["operations handbook"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    topic1 --> foundation
    topic2 --> foundation
    topic3 --> foundation
    foundation --> next1
    foundation --> next2
    foundation --> next3
    class foundation page;
    class topic1,topic2,topic3 positive;
    class next1,next2,next3 anchor;
```

## Pages In This Section

- [Platform Overview](platform-overview.md)
- [Repository Scope](repository-scope.md)
- [Workspace Layout](workspace-layout.md)
- [Package Map](package-map.md)
- [Ownership Model](ownership-model.md)
- [Domain Language](domain-language.md)
- [Documentation System](documentation-system.md)
- [Change Principles](change-principles.md)
- [Decision Rules](decision-rules.md)

## Purpose

This page gives readers a clean starting point for the repository foundation.

## Stability

Keep it aligned with the actual foundation topics that define the repository
boundary and package split.
