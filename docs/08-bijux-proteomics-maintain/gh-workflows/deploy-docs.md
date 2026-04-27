---
title: deploy-docs
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# deploy-docs

`deploy-docs.yml` owns handbook publication. It should make public-doc publication predictable and auditable.

## What To Check

- trigger conditions for publishing docs from the intended branch
- which build and verification steps run before publication
- how docs deployment failure is distinguished from product-package failures

## First Proof Check

- `.github/workflows/deploy-docs.yml`
- docs verification commands referenced by the workflow
