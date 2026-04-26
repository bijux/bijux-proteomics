---
title: Platform Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Platform Overview

`bijux-proteomics` is a multi-package system because protein-program design is
easier to trust when runtime control, shared primitives, domain contracts,
decision logic, evidence handling, and lab execution stay distinct.

Read the platform as a chain of responsibilities rather than as a directory
list. Foundation stabilizes shared payload meaning. Core defines program and
lifecycle contracts. Knowledge tracks evidence and claims. Intelligence turns
those inputs into inspectable decisions. Lab turns decisions into assay work.
`bijux-proteomics-runtime` governs execution, replay, and final runtime
behavior. `agentic-proteins` remains as a compatibility surface.

```mermaid
flowchart LR
    foundation["foundation<br/>shared meaning"]
    core["core<br/>program contracts"]
    knowledge["knowledge<br/>evidence and claims"]
    intelligence["intelligence<br/>decision policy"]
    lab["lab<br/>assay planning and outcomes"]
    runtime["runtime<br/>execution and replay"]
    compat["agentic-proteins<br/>legacy compatibility"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    foundation --> core --> knowledge --> intelligence --> lab --> runtime --> compat
    class foundation,core,knowledge,intelligence,lab,runtime positive;
    class compat caution;
```

## Why The Split Matters

- ownership is clearer during review
- package contracts stay narrower and easier to defend
- cross-package seams stay visible instead of becoming accidental coupling

