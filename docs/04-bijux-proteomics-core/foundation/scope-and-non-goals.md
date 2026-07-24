---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Scope And Non-Goals

`bijux-proteomics-core` is the scientific engine and contract library. Its
scope follows proteomics meaning rather than application workflow: an operation
belongs here when its result and failure boundary can be defined without
provider selection, execution state, evidence policy, recommendation posture,
or laboratory capacity.

## In Scope

- parsing and validation of scientific formats and exported results;
- sequence, peptide, modification, mass, spectrum, and database operations;
- identification confidence, FDR, protein inference, and ambiguity;
- quantitative normalization, missingness, comparison, and QC;
- DIA, LFQ, multiplex, PTM, targeted, and DDA scientific surfaces;
- deterministic reports and portable scientific artifacts;
- benchmark packages, comparator evidence, acceptance bars, and challenge
  corpora;
- Python and file-oriented CLI interfaces over the same scientific owners.

## Explicit Non-Goals

| Concern | Owner |
| --- | --- |
| universal identifiers, document metadata, canonical JSON | Foundation |
| processes, providers, state, retries, checkpoints, replay | Runtime |
| claims, citations, contradictions, biological evidence custody | Knowledge |
| candidate ranking, confidence, recommendation, refusal | Intelligence |
| assay feasibility, scheduling, handoff, observation, promotion | Lab |
| legacy Runtime namespace compatibility | Agentic Proteins |
| repository quality, generated governance, release automation | Maintainer tooling |

Core is not a vendor pipeline emulator. Import adapters can preserve declared
semantics and field loss without proving external-engine parity. Benchmark
fixtures can challenge a method without proving universal transfer. Biological
interpretation can compute a result without becoming a curated evidence store
or a recommendation.

## Growth Rule

New scientific capability requires an owned domain boundary, explicit input
and output contracts, units and orientation, rejected-input evidence, QC,
limitations, focused tests, and a public navigation route. Avoid adding thin
peer modules when the capability belongs to an existing scientific domain.

The Core public surface should grow by scientific responsibility, not by one
file per delivery request or one wrapper per caller.
