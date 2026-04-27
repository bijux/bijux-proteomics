---
title: Change Principles
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Change Principles

Changes in `bijux-proteomics-lab` should make lab-facing execution more explicit, not more mixed.
If a change needs several different justifications, it probably spans too many
owners.

## Principles

- strengthen one named role per change set
- move proof with the behavior when docs, contracts, or tests also change
- reject shortcuts that make neighboring package boundaries less visible

## First Proof Check

- the local package tests
- the matching handbook pages
- neighboring packages if the change alters a handoff seam
