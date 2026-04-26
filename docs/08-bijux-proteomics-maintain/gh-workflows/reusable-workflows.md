---
title: reusable-workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# reusable-workflows

Reusable workflows exist to keep shared automation logic explicit instead of duplicating it across triggers.

## What To Check

- which top-level workflows call reusable workflow files
- which inputs, matrices, or permissions are centralized there
- whether reuse is clarifying automation or hiding ownership

## First Proof Check

- `.github/workflows/ci.yml`
- other workflow files that call it

