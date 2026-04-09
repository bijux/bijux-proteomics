---
title: Review Expectations
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Review Expectations

Root review should be sharper than purely local code review because repository
changes can alter how the whole package family is built, read, or released.

## Root Review Expectations

- confirm the owning repository surface is still the right one for the change
- check that docs, automation, and proof assets move together
- verify that the change does not smuggle product behavior into root or
  maintainer automation
- prefer clear, durable commit intent over vague shorthand

## Purpose

This page records the review bar for repository-wide changes.

## Stability

Keep it aligned with the actual root review posture and proof surfaces.
