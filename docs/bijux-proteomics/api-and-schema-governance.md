---
title: API and Schema Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-04
---

# API and Schema Governance

Shared API artifacts live under `api/` so contract review does not depend on
reading package source alone. A caller or reviewer should not need to reverse-
engineer Python modules just to understand whether an HTTP or artifact
contract changed.

## How A Public Contract Change Should Move

```mermaid
sequenceDiagram
    participant Code as package code
    participant API as api/
    participant Review as review
    participant Checks as drift checks and tests
    participant Release as release

    Code->>API: update tracked schema or artifact
    API->>Review: make the contract diff visible
    Review->>Checks: require proof that code and schema still agree
    Checks->>Release: allow shipping only when the surfaces align
    Release-->>Code: preserve one public story instead of two
```

## Governance Rules

- package code and tracked schema files must describe the same public behavior
- drift checks belong in shared gates or package tests, not in prose alone
- schema hashes and pinned OpenAPI artifacts should move only with reviewable intent

## Current Schema Roots

- `apis/agentic-proteins/v1/schema.yaml` for public runtime API contracts
- package-local model schemas under `packages/*/src/**/schema.py`
- package-local changelog and metadata links as release-facing contract references

One public contract should have one reviewable story. If code, schema files,
and release artifacts disagree, the docs are not the thing that will save us.
