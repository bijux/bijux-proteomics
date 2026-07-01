---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-01
---

# Package Overview

`bijux-proteomics-foundation` owns the low-volatility meaning that every other
package consumes before it can do anything scientific: identifiers, shared
payload schemas, canonical JSON, deterministic fingerprints, compatibility
profiles, and outcome-safe document evolution.

The package is intentionally narrow, but it is not a placeholder. The broader
scientific product only stays coherent because every downstream owner can rely
on one stable family of identifiers, one serialization story, and one
compatibility discipline instead of inventing local dialects.

## Why This Package Matters More Now

- `bijux-proteomics-core` now carries far more sequence, chemistry, spectra,
  DIA, PTM, and quantification depth, so shared-model drift costs more than it
  did in earlier releases
- `bijux-proteomics-runtime` now exposes replayable and auditable public runs,
  so unstable serialization would damage public rerun proof instead of only
  internal automation
- `bijux-proteomics-knowledge`, `...-intelligence`, and `...-lab` now pass
  richer claim, consequence, and outcome state, which makes identifier and
  compatibility discipline a product concern rather than an implementation
  detail

## Concrete Owner Surfaces

| owner surface | current substance | why readers should care |
| --- | --- | --- |
| `identity` | stable identifiers and typed keys | downstream packages can refer to the same scientific objects without drift |
| `compatibility` | schema profiles, version checks, and upgrade discipline | release and migration language can stay honest |
| `serialization` | canonical JSON, stable rendering, and reproducible hashing | artifacts can be compared, replayed, and audited repeatably |
| `outcomes` | shared outcome carriers and result-shape primitives | outcome state stays family-compatible instead of becoming package-local prose |
| `support` and `testing` | common helpers and test-facing primitives | invariants are enforced consistently across packages |

## What It Owns

- define shared identifiers
- govern schema profiles and serialization compatibility
- carry deterministic hashing and payload fingerprint rules
- carry migration helpers for payload evolution and cross-package invariants
- expose shared outcome and support primitives that let downstream packages
  exchange state without rewriting the family contract

## What It Refuses

- program lifecycle or benchmark-acceptance policy
- evidence truth, contradiction handling, or recommendation posture
- execution orchestration, replay, or assay consequence logic

## What Readers Commonly Underestimate

- this package is the reason runtime rerun artifacts and knowledge-review
  artifacts can be compared without local translation glue
- this package keeps release upgrades from silently changing the meaning of
  payloads that later look "compatible" only because tests stayed shallow
- this package owns the family contract below the biological and analytical
  story, not above it

## Strongest Reader Route

- start here when the question is whether two packages can exchange one object
  family without ambiguity
- continue to the architecture and interface pages when the concern is schema
  layout, public payloads, or compatibility commitments
- hand off to `core`, `knowledge`, `runtime`, `intelligence`, or `lab` only
  after the shared meaning layer is no longer the risk

## First Proof Check

- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation`
- `packages/bijux-proteomics-foundation/tests`
- tracked APIs and schema-facing artifacts once a change reaches public
  contracts
- neighboring handbook branches once a change crosses the local role
