---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-13
---

# CLI Surface

CLI documentation should describe the commands the package truly owns, not the commands a reader might wish existed.

## Package Surface

- `src/bijux_proteomics/interfaces/cli/app.py` and `interfaces/cli/__main__.py` are the command-line surfaces for core contract workflows
- CLI behavior should reveal contract meaning and validation state rather than runtime orchestration detail
- new CLI promises must stay aligned with the stable contract model

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/interfaces/cli/app.py` and `interfaces/cli/__main__.py`
- `packages/bijux-proteomics-core/tests`

## FASTA Commands

The owned FASTA CLI surface is:

- `fasta-parse`
- `fasta-stats`
- `fasta-dedup`
- `fasta-filter`
- `fasta-provenance`
- `fasta-decoy`
- `target-decoy-validate`
- `summarize --kind fasta`

`fasta-parse` emits the full parser report, including:

- accepted and rejected records
- duplicate identifiers
- duplicate normalized accessions
- parser-level database composition over accepted records

The database composition surface reports:

- accepted record count
- target count
- decoy count
- contaminant count
- accession-namespace counts

`fasta-stats` reports FASTA-wide review metrics such as duplicate accession
count, duplicate sequence count, target count, decoy count, contaminant count,
and sequence-length summary values.

`summarize --kind fasta` returns both the higher-level FASTA summary and the
parser-level database composition so operators can distinguish structural file
quality from biological database makeup.
