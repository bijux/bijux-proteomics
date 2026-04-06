---
title: Workspace Layout
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-04
---

# Workspace Layout

The tree should help people place work quickly. If the layout makes ownership
harder to see, it is working against the design instead of supporting it.

## The Top-Level Shape

```mermaid
flowchart TB
    repo["bijux-proteomics"]
    packages["packages/<br/>publishable distributions"]
    apis["apis/<br/>package OpenAPI contracts and pinned artifacts"]
    docs["docs/<br/>human-facing handbook"]
    makes["makes/ and Makefile<br/>workspace automation"]
    configs["configs/<br/>tooling configuration"]
    artifacts["artifacts/<br/>generated outputs and checks"]

    repo --> packages
    repo --> apis
    repo --> docs
    repo --> makes
    repo --> configs
    repo --> artifacts
```

## Top-Level Directories

- `packages/` for publishable Python distributions
- `apis/` for per-package schema sources, pinned OpenAPI JSON, and schema digests
- `docs/` for the canonical handbook
- `makes/` and `Makefile` for workspace automation
- `artifacts/` for generated or checked validation outputs
- `configs/` for root-managed tool configuration

## Layout Rule

A concern should live at the root only when it serves more than one package or
when it is about the workspace itself.

The root should explain the workspace. It should not become a quiet backdoor
for product behavior.
