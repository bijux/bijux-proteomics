---
title: Review Expectations
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Review Expectations

Root review should be sharper than purely local code review because repository
changes can alter how the whole package family is built, read, or released.

```mermaid
flowchart LR
    change["root change under review"]
    owner["right owning surface?"]
    coupled["docs, automation, and proof moved together?"]
    scope["product behavior kept out of root?"]
    approve["approve when evidence is coherent"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    change --> owner --> coupled --> scope --> approve
    class approve page;
    class change,owner,coupled,scope action;
```

## Root Review Expectations

- confirm the owning repository surface is still the right one for the change
- check that docs, automation, and proof assets move together
- verify that the change does not smuggle product behavior into root or
  maintainer automation
- prefer clear, durable commit intent over vague shorthand

## Purpose

This page records the review bar for repository-wide changes.

## Stability

Keep it aligned with the actual root review posture and proof surfaces.
