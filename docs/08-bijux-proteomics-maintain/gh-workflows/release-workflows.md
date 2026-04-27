---
title: release-workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# release-workflows

Release workflows are the irreversible automation surfaces. Their job is to publish only after repository proof is already complete.

## What To Check

- the split between artifact, GitHub, PyPI, and GHCR publication workflows
- the tag and permission assumptions behind each publication path
- whether release automation still matches maintainer release policy

## First Proof Check

- `.github/workflows/release-artifacts.yml`
- `.github/workflows/release-github.yml`, `release-pypi.yml`, and `release-ghcr.yml`
