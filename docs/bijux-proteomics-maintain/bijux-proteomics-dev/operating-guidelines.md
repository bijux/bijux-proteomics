---
title: Operating Guidelines
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Operating Guidelines

Changes in `bijux-proteomics-dev` deserve extra care because the package can
affect multiple publishable packages at once.

Repository-health automation should therefore bias toward explicit scope,
explicit tests, and explicit explanations. A small maintainer change should not
need detective work to understand its package impact.

## Guidelines

- prefer checked-in Python helpers over opaque shell glue
- make package impact visible in code, docs, and commit history
- keep maintainer-only guidance here instead of leaking it into product package
  docs
- update the relevant tests and handbook pages in the same change series

## Purpose

This page records the expected maintenance posture for repository-health work.

## Stability

Update it only when the repository operating model genuinely changes.
