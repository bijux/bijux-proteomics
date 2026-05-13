---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-13
---

# Common Workflows

Common workflows should sound like the real jobs people do with the package, not generic process filler.

## Operating Rules

- review a program or target contract change against lifecycle and execution rules
- check whether runtime consumers need explicit downstream validation
- update contract-facing docs with the same discipline as the code change

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py` and `domain/targets.py`
- `src/bijux_proteomics/domain/lifecycle.py` and `domain/validation.py`
- `packages/bijux-proteomics-core/tests`

## FASTA Intake

Use the FASTA intake surface before digestion, target-decoy preparation, or
search-database review whenever a protein database may contain mixed header
styles, contaminants, decoys, or lab-local records.

- `fasta-parse` returns accepted and rejected records, duplicate identifiers,
  duplicate normalized accessions, and parser-level database composition.
- Empty-sequence records are rejected explicitly instead of aborting the whole
  file.
- UniProt, RefSeq, Ensembl, and custom lab headers can coexist in one parse
  report.
- Target-decoy and contaminant-heavy databases remain reviewable because the
  accepted-record composition reports target, decoy, and contaminant counts.

The parser contract is intentionally stricter than a line reader. Its job is
to tell the operator whether the database is usable for downstream proteomics
work, not just whether the file is syntactically FASTA-like.

## FASTA Database Profiling

Use `fasta-profile` when the question is not just whether a database parses,
but what kind of search or digestion burden it will create.

- The profile summary reports total input records, accepted proteins, rejected
  records, unique accessions, target count, decoy count, contaminant count,
  and organism annotation coverage.
- The length-distribution ledger bins proteins into stable ranges so long-form
  sequence burden is visible before digestion or search.
- The organism-distribution ledger aggregates proteins by parsed organism name
  when the header carries that evidence.
- The profile can be exported as one JSON object plus dedicated TSV ledgers for
  summary, length distribution, and organism distribution.

This profiling surface is intentionally reviewer-facing. It helps operators
decide whether a database is appropriately scoped and annotated before they
commit to downstream evidence generation.

## Contaminant Database Assembly

Use `fasta-contaminants` when a target-only FASTA is not realistic enough for
search or digestion review on its own.

- The owned built-in contaminant panel appends common carryover proteins such
  as albumin, trypsin, and keratins.
- External contaminant FASTA files can be appended in the same run for
  lab-local contaminants.
- Appended contaminant proteins are relabeled with the stable `CON__` prefix so
  downstream search evidence can distinguish them from targets.
- The build report separates built-in versus external contaminant counts and
  records skipped duplicate contaminant accessions.

After search import, use the contaminant-match review surface to separate
contaminant-carrying PSMs from target-only evidence instead of letting those
matches disappear into the general peptide summary.
