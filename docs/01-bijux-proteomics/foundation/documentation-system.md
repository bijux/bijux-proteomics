---
title: Documentation System
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Documentation System

The root documentation site is the canonical handbook for repository and
package behavior. It should help a new reader understand the package split,
choose the right handbook branch, and verify claims from checked-in assets
without guesswork.

Use the docs as orientation first and proof map second. Repository pages should
explain cross-package concerns, while package pages, schemas, tests, and
release artifacts carry the detailed evidence behind specific claims.

```mermaid
flowchart TD
    site[Docs site]
    landing[landing page]
    repo[repository handbook]
    pkg[package handbooks]
    maintain[maintainer handbook]
    proof[schemas tests metadata workflows]

    site --> landing
    site --> repo
    site --> pkg
    site --> maintain

    repo -->|orientation| proof
    pkg -->|detailed behavior| proof
    maintain -->|repo health checks| proof
```

## Handbook Shape

- one landing page for site orientation
- one repository handbook for cross-package rules and shared assets
- one five-category handbook per product package
- one maintainer handbook for repository-health automation

## Documentation Rules

- use stable filenames that describe durable intent
- keep package handbooks on the same five-category spine
- separate repository docs from maintainer docs
- update docs in the same change series as the behavior they explain

## Purpose

Use this page to understand how the handbook is organized and where
repository-level guidance should stop.

## Stability

Keep it aligned with the sections and navigation the site actually renders.
