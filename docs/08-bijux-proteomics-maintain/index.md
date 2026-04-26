---
title: Maintainer Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Maintainer Handbook

`bijux-proteomics-maintain` is the repository-health handbook. Open it when the question is above any one product package and the answer lives in maintainer helper code, workflow contracts, or the shared command surface.

## Start With

- open [bijux-proteomics-dev](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/) when the rule is implemented as checked-in Python maintainer code
- open [gh-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/) when the symptom starts from GitHub automation
- open [makes](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/) when the question starts from `make`, CI target routing, or release command fan-out

## What This Handbook Owns

- repository-wide proof, publication, docs integrity, security, and policy enforcement
- shared command routing and GitHub automation contracts
- the boundary between package handbooks and repository-health surfaces

## First Proof Check

- `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/`
- `.github/workflows/`
- `Makefile` and `makes/`

