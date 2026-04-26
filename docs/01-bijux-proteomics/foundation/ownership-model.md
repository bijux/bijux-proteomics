---
title: Ownership Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Ownership Model

The repository is easiest to trust when ownership can be stated in layers
without hesitation.

The product packages own runtime and domain behavior. The repository root owns
only what genuinely crosses package boundaries: shared docs structure, schema
governance, validation coordination, and release framing. The maintenance
handbook exists for repository health, not for product behavior.

```mermaid
flowchart LR
    root["repository root<br/>docs, CI, release framing"]
    maintain["bijux-proteomics-dev<br/>maintainer automation"]
    packages["product packages<br/>publishable behavior"]
    runtime["runtime and domain logic<br/>owned in packages"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    root --> maintain
    root --> packages
    packages --> runtime
    class root page;
    class maintain anchor;
    class packages,runtime positive;
```

## Ownership Layers

- canonical runtime behavior belongs in `packages/bijux-proteomics-runtime`
- compatibility forwarding behavior belongs in `packages/agentic-proteins`
- domain behavior belongs in `packages/bijux-proteomics-*` lower-layer packages
- shared governance belongs in the repository handbook and root automation
- maintainer automation belongs in `packages/bijux-proteomics-dev` and the
  maintenance handbook

