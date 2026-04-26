---
title: Documentation System
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Documentation System

The root documentation site is the canonical handbook for repository and
package behavior. It should help a new reader understand the package split,
choose the right handbook branch, and verify claims from checked-in assets
without guesswork.

Use the docs as orientation first and proof map second. Repository pages cover
cross-package concerns, while package pages, schemas, tests, and release
artifacts carry the detailed evidence behind specific claims.

```mermaid
flowchart TB
    site["Docs site"]
    landing["landing page"]
    repo["repository handbook"]
    package["package handbooks"]
    maintain["maintainer handbook"]
    proof["schemas, tests, metadata, workflows"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    site --> landing
    site --> repo
    site --> package
    site --> maintain
    repo --> proof
    package --> proof
    maintain --> proof
    class site page;
    class landing,repo,package,maintain anchor;
    class proof action;
```

## Handbook Shape

- one landing page for site orientation
- one repository handbook for cross-package rules and shared assets
- one five-category handbook per product package
- one maintainer handbook for repository-health automation

## Published Handbook Sections

- `https://bijux.io/bijux-proteomics/01-bijux-proteomics/` for repository-wide
  rules and shared assets
- `https://bijux.io/bijux-proteomics/02-agentic-proteins/` through
  `https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/` for package
  handbooks
- `https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/` for
  repository-health automation
- `https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/` for runtime
  migration and ownership review

## Documentation Rules

- use stable filenames that describe durable intent
- keep package handbooks on the same five-category spine
- separate repository docs from maintainer docs
- update docs in the same change series as the behavior they explain

## Purpose

This page shows how the handbook is organized and where repository-level
guidance should stop.

## Stability

Keep it aligned with the sections and navigation the site actually renders.
