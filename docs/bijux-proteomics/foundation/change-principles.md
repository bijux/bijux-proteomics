---
title: Change Principles
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Change Principles

Root-level change should leave the repository easier to explain, not merely
more featureful.

## Principles

- prefer moving behavior toward the owning package rather than broadening root
  scope for convenience
- keep docs, schema artifacts, tests, and automation updates in the same review
  series when they describe the same behavior
- choose filenames, headings, and commit messages that will still make sense
  years later
- keep repository automation explicit about what it touches and why

## Architecture Invariants

- package boundaries remain explicit and import directions stay acyclic
- domain runtime code and maintainer tooling stay in separate packages
- repository-wide checks remain deterministic for identical repository state

## Purpose

This page records the principles that should guide repository-wide change.

## Stability

Update it only when the repository operating model changes in a real way.
