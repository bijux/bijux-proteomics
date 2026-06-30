---
title: Repository Shape Rationale
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-09
---

# Repository Shape Rationale

This repository is split by durable owner questions, not by delivery sequence.
The split is justified only when a skeptical reader can explain why one package
must remain distinct from its neighbors and why one compatibility layer should
eventually disappear.

## Durable Splits

| package | durable reason to stay distinct | failure if collapsed |
| --- | --- | --- |
| `bijux-proteomics-foundation` | shared identifiers, serialization, and migration-safe document rules | higher packages would quietly fork payload meaning |
| `bijux-proteomics-core` | workflow contracts, lifecycle rules, and benchmark-facing scientific law | runtime or review layers would become shadow owners of domain truth |
| `bijux-proteomics-runtime` | execution control, replay, operator entrypoints, and run artifacts | scientific owners would inherit transport and provider logic |
| `bijux-proteomics-knowledge` | cited evidence memory, contradiction handling, and reference-grounded review state | intelligence and lab would rebuild private trust models |
| `bijux-proteomics-intelligence` | recommendation posture, downgrade logic, and refusal behavior | ranking policy would blur into evidence storage or lab action |
| `bijux-proteomics-lab` | assay consequence, readiness, burden, and observed-outcome follow-through | recommendation language would overstate downstream executability |

## Temporary Compatibility Split

`agentic-proteins` is not a seventh product owner. It remains only as a legacy
compatibility bridge for historical runtime imports and entrypoints. New
behavior should land in canonical owners first, then forward from compat only
when migration continuity still matters.

## Candidate Future Merges

- Merge a seam only when the weaker package stops owning a question that the
  stronger package cannot answer without duplicating the same proof.
- Do not merge foundation into core while deterministic serialization,
  identifiers, and migration discipline still need a low-volatility owner.
- Do not merge runtime into core or intelligence while execution control and
  replay proof still need to stay runtime-specific.
- Do not merge knowledge into intelligence or lab while evidence truth and
  contradiction state still need to remain distinct from recommendation or
  consequence policy.

## First Checks

- Open [Cross-Package Ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
  for the current handoff map.
- Open [Package Map](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/package-map/)
  for the shortest owner-routing table.
- Open [DDA Cross-Package Handbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/dda-cross-package-handbook/)
  for one concrete benchmark path that exercises all six product packages.
