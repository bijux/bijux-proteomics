---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-foundation` owns the low-volatility primitives every product
package shares: identifiers, schema profiles, canonical JSON, stable hashes,
and migration-safe document rules. The package is only healthy when that owner
story stays narrow enough that a reviewer never has to mention ranking,
execution, benchmark acceptance, or lab consequence to explain why it exists.

## What It Owns

- define shared identifiers
- govern schema profiles and serialization compatibility
- carry deterministic hashing and payload fingerprint rules
- carry migration helpers for payload evolution and cross-package invariants

## What It Refuses

- program lifecycle or benchmark-acceptance policy
- evidence truth, contradiction handling, or recommendation posture
- execution orchestration, replay, or assay consequence logic

## First Proof Check

- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation`
- `packages/bijux-proteomics-foundation/tests`
- neighboring handbook branches once a change crosses the local role
