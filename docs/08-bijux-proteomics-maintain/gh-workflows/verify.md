---
title: verify
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# verify

`verify.yml` is the push and pull-request gate. It should answer whether the repository still meets its checked-in proof rules before merge.

## What To Check

- trigger paths for branch and pull-request verification
- how `verify.yml` delegates into reusable CI logic such as `ci.yml`
- which failures belong to maintainer policy versus product-package proof

## First Proof Check

- `.github/workflows/verify.yml`
- `.github/workflows/ci.yml`

