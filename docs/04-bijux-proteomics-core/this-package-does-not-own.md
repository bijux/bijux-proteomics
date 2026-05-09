---
title: This Package Does Not Own
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# This Package Does Not Own

Package: `bijux-proteomics-core`  
Import root: `bijux_proteomics`

Core owns durable scientific contracts and workflow rules. It should not turn
into the place where evidence truth, recommendation posture, or execution
delivery quietly re-accumulate.

## Supported Package-Root Imports

- `DigestPolicy`
- `parse_fasta_document`
- `parse_experimental_design_table`
- `build_normalized_run_bundle`
- `build_fdr_audit_trail`

## Allowed Package Dependencies

- `bijux-proteomics-foundation`
- `bijux-proteomics-intelligence`
- `bijux-proteomics-knowledge`
- `bijux-proteomics-lab`
- `bijux-proteomics-runtime`

These edges are governed because benchmark acceptance and workflow contracts
need reviewed reference support plus narrow downstream seams, but the package
must still stay the owner of runtime-agnostic scientific rules.

## Excluded Responsibilities

- evidence trust and contradiction resolution
- ranking policy and scenario recommendations
- experiment scheduling and assay rerun policy logic

## Route Elsewhere

- Use `bijux-proteomics-knowledge` when the work changes reference support,
  contradiction state, or scientific memory.
- Use `bijux-proteomics-intelligence` when the work changes refusal posture,
  ranking sensitivity, or recommendation language.
- Use `bijux-proteomics-runtime` when the work changes replay bundles,
  operator transport, or provider execution behavior.
