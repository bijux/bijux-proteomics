---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Domain Language

Stable language is part of the repository design.

When terms drift, readers stop knowing whether they are talking about a package
contract, a repository rule, or a maintainer-only concern. That confusion
rebuilds architectural blur even when the tree still looks tidy.

```mermaid
flowchart LR
    term1["repository handbook"]
    term2["maintainer handbook"]
    term3["proof surface"]
    language["Stable repository language"]
    reader1["review routing"]
    reader2["clear ownership"]
    reader3["fewer false assumptions"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    term1 --> language
    term2 --> language
    term3 --> language
    language --> reader1
    language --> reader2
    language --> reader3
    class language page;
    class term1,term2,term3 anchor;
    class reader1,reader2,reader3 positive;
```

## Terms That Stay Stable

- `repository handbook` for cross-package governance and structure
- `maintainer handbook` for repository-health automation and operations
- `canonical package` for one of the publishable product distributions
- `proof surface` for the files that let a reader verify a claim, such as
  tests, schema artifacts, metadata, or workflow definitions

