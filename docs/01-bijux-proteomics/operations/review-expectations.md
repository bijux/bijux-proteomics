---
title: Review Expectations
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Review Expectations

Root review should be stricter than a purely local code review because repository
changes can alter how the whole package family is explained, validated, or
released.

## Non-Negotiable Evidence

- the change lives in the right owning surface
- docs, schema artifacts, metadata, and automation move together when they
  describe the same behavior
- package-local behavior is not smuggled into root or maintainer automation
- the best proof surface is named directly, not implied

## First Proof Check

- the owning handbook branch
- the matching code, tests, tracked artifacts, or workflow files
- staged diff boundaries before commit so one intent stays one review unit
