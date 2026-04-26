---
title: bijux-proteomics-foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-foundation

`bijux-proteomics-foundation` owns shared payload meaning in
`bijux-proteomics`. It keeps identifiers, schema compatibility, migrations, and
deterministic serialization stable enough that the rest of the package family
can exchange meaning without ambiguity.

## What It Owns

- identifiers and shared payload primitives
- schema and serialization compatibility helpers
- migration rules for shared payload evolution

## What It Refuses

- program policy and lifecycle decisions
- evidence truth and contradiction state
- execution, provider, or operator-facing runtime behavior

## Start With

- Open [Foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/)
  for the package role and boundary.
- Open [Interfaces](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/)
  when the question is a public contract or shared data surface.
- Open [bijux-proteomics-core](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
  when the concern becomes program behavior rather than shared meaning.

## First Proof Check

- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation`
- `packages/bijux-proteomics-foundation/tests`
- tracked artifacts under `apis/` when the change reaches a public contract
