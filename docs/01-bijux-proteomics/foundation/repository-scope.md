---
title: Repository Scope
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Repository Scope

The root should stay boring in the best possible way. When repository files
start absorbing product behavior, every package boundary becomes harder to
trust.

```mermaid
flowchart TD
    A[Proposed root change] --> B{Does it span multiple packages?}
    B -->|Yes| C{Is it about governance / shared docs / CI / APIs?}
    B -->|No| D[Keep it in the owning package]
    C -->|Yes| E[Root scope]
    C -->|No| D
    E --> E1[shared automation]
    E --> E2[repository handbook]
    E --> E3[checked API artifacts]
    E --> E4[release rules]
    D --> D1[package-local runtime behavior]
    D --> D2[package-local internals]
    D --> D3[undocumented helper logic]
```

## In Scope

- workspace-level automation and shared validation
- root handbook structure and repository-wide governance
- checked API artifacts under `apis/`
- release, docs, and CI rules that genuinely span packages

## Out Of Scope

- package-local runtime behavior
- quiet root helpers that bypass package APIs
- undocumented exceptions to the package ownership model

## Purpose

This page explains what the repository root is allowed to own.

## Stability

Keep it aligned with the current division between repository governance and
package-owned behavior.
