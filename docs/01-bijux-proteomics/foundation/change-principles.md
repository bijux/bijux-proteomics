---
title: Change Principles
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Change Principles

Root-level change should leave the repository easier to explain, not merely
more featureful.

```mermaid
flowchart LR
    proposal["proposed root change"]
    own["move behavior toward the right owner"]
    coupled["docs, schema, tests,<br/>and automation move together"]
    names["names stay durable"]
    review["change is reviewable"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    proposal --> own --> coupled --> names --> review
    class review page;
    class proposal,own,coupled,names action;
```

## Principles

- prefer moving behavior toward the owning package rather than broadening root
  scope for convenience
- keep docs, schema artifacts, tests, and automation updates in the same review
  series when they describe the same behavior
- choose filenames, headings, and commit messages that will still make sense
  years later
- keep repository automation explicit about what it touches and why

## Architecture Invariants

- package boundaries remain explicit and import directions stay acyclic
- domain runtime code and maintainer tooling stay in separate packages
- repository-wide checks remain deterministic for identical repository state

