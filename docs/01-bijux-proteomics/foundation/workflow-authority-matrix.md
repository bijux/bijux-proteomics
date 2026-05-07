---
title: Workflow Authority Matrix
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Workflow Authority Matrix

This page is the release-facing authority source of truth for the flagship
workflow families.

Outsider-auditable workflow families today: `dda`, `dia`, `lfq`, `ptm`, `targeted`.
Internal-support-only workflow families today: `multiplex`.

## Current Authority

| Workflow | Internal benchmark-backed | Raw-executable | Externally cross-checked | Outsider-auditable | Lab-consequential | Public language |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `dda` | yes | no | yes | yes | yes | bounded outsider-auditable |
| `dia` | yes | yes | yes | yes | yes | bounded outsider-auditable |
| `lfq` | yes | yes | yes | yes | yes | bounded outsider-auditable |
| `multiplex` | yes | yes | no | no | no | internal support only |
| `ptm` | yes | yes | yes | yes | yes | bounded outsider-auditable |
| `targeted` | yes | yes | yes | yes | yes | bounded outsider-auditable |

## How To Read This

- `internal benchmark-backed` means a tracked flagship public package exists
  under `benchmark-assets/flagship-public-packages/`
- `raw-executable` means the strongest current runtime lane runs the tracked
  package directly instead of stopping at an import-only bridge
- `externally cross-checked` means public comparator posture is at least
  advisory rather than refused
- `outsider-auditable` means the benchmark package, runtime lane, scientific
  reading, recommendation packet, and lab packet can be opened together by a
  skeptical reviewer
- `lab-consequential` means a dedicated flagship lab packet exists, even when
  the packet still keeps the family exploratory-only

## Boundary

This matrix does not grant elite language. It only narrows what each workflow
family can honestly claim today.
