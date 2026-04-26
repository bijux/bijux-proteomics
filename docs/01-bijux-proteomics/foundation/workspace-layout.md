---
title: Workspace Layout
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Workspace Layout

The top-level tree should help readers place work quickly. If the layout makes
ownership harder to see, it is working against the design.

```mermaid
flowchart TB
    repo["bijux-proteomics"]
    packages["packages/<br/>publishable code"]
    apis["apis/<br/>checked contract artifacts"]
    docs["docs/<br/>canonical handbook"]
    makes["Makefile and makes/<br/>shared automation"]
    configs["configs/<br/>tool configuration"]
    artifacts["artifacts/<br/>generated output only"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    repo --> packages
    repo --> apis
    repo --> docs
    repo --> makes
    repo --> configs
    repo --> artifacts
    class repo page;
    class packages,apis,docs,makes,configs anchor;
    class artifacts action;
```

## Top-Level Directories

- `packages/` for publishable Python distributions and maintainer tooling
- `apis/` for checked schema sources, pinned OpenAPI JSON, and digests
- `docs/` for the canonical handbook
- `makes/` and `Makefile` for repository automation
- `configs/` for shared tool configuration
- `artifacts/` for generated validation output

## Layout Rule

A concern should live at the root only when it serves more than one package or
when it explains the workspace itself.

## Purpose

This page explains the top-level directory split that supports the repository
ownership model.

## Stability

Keep it aligned with the real top-level directories and their current meaning.
