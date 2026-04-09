---
title: Environment Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Environment Model

The make system should make environment assumptions visible instead of smearing
them across unrelated targets.

Repository behavior depends on shared environment fragments such as
`makes/env.mk`, `makes/bijux-py/root/env.mk`, and
`makes/bijux-py/repository/env.mk`. Those files define variables and execution
assumptions that later targets depend on.

## Environment Rules

- centralize shared variables instead of redefining them in many fragments
- keep package-independent environment logic in shared files
- make local and CI execution assumptions easy to compare

## Purpose

This page explains where shared environment expectations live in the make
system.

## Stability

Keep it aligned with the environment fragments currently present under
`makes/`.
