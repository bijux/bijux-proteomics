---
title: Automation Surfaces
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Automation Surfaces

Repository automation should be visible in named surfaces, not hidden behind
tribal shortcuts.

```mermaid
flowchart TB
    auto["Repository automation"]
    makefile["Makefile<br/>entrypoint"]
    makes["makes/<br/>shared fragments"]
    workflows[".github/workflows/<br/>CI and release"]
    devpkg["bijux-proteomics-dev<br/>code-bearing helpers"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    auto --> makefile
    auto --> makes
    auto --> workflows
    auto --> devpkg
    class auto page;
    class makefile,makes,workflows,devpkg anchor;
```

## Core Automation Surfaces

- `Makefile` as the top-level repository entrypoint
- `makes/` as the structured library of shared make fragments
- `.github/workflows/` as the published CI, docs, and release automation
- `packages/bijux-proteomics-dev` as the code-bearing home for maintainer
  helpers

## Purpose

This page shows where repository automation is allowed to live and how it
stays reviewable.

## Stability

Keep it aligned with the actual automation surfaces contributors are expected
to use.
