---
title: Code Navigation
audience: developer
type: architecture
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Code Navigation

Bijux Proteomics Core is the scientific heart of the suite. Navigate by the
scientific question, not by searching the package root: the implementation is
divided into explicit domain families spanning raw evidence, identification,
quantification, study design, PTMs, interpretation, review, and workflow
artifacts.

## Domain map

| Question | Start here | What the family owns |
| --- | --- | --- |
| What constitutes a program, target, gate, or valid progression? | `domain/` | scientific program state, records, confidence, semantic identifiers, targets, and validation |
| How are proteins and peptides represented? | `sequences/` and `chemistry/` | FASTA, digestion, protein identity, masses, modifications, fragments, isotopes, and chemical liabilities |
| How does instrument or tabular evidence enter? | `io/` | governed formats, tables, spectra, chromatograms, raw-signal evidence, and input integrity |
| How do search-engine results become comparable? | `identification/adapters/` and `identification/search_adapters/` | engine dialects, normalization, field accounting, provenance, conformance, and loss |
| How are PSM, peptide, and protein claims controlled? | `identification/contracts/`, `psm/`, `peptide/`, `protein/`, and `fdr/` | evidence levels, target-decoy error control, grouping, parsimony, ambiguity, and coverage |
| How are abundance matrices built and tested? | `quantification/` | rollup, normalization, missingness, statistics, contributor decomposition, and provenance |
| How is experimental design represented? | `study/` | sample metadata, contrasts, batches, replicate structure, and design validity |
| How are PTM and DIA results handled? | `ptm/`, `dia/`, `isotope_labeling/`, and `multiplex/` | site parsing and localization, PTM quantification, precursor evidence, labeling, and channel-aware analysis |
| How are biological outputs bounded? | `interpretation/`, `biology/`, `panels/`, `proteoforms/`, and `targeted/` | enrichment, activity, networks, contextual annotations, assays, and validation planning |
| How does evidence reach a reviewer? | `review/` and `workflow/` | claims, belief and evidence graphs, cards, reports, pipelines, governed exports, and benchmark studies |

## Public entry routes

Use `interfaces/python_api/` for application composition and `interfaces/cli/`
for commands. Both should terminate in the same owning scientific families.
`interfaces/execution/` is the narrow seam for executing a validated program
through a supplied backend; it is not a second scientific implementation.

The root package contains compatibility facades as well as owned modules. When
a file says it is a compatibility facade, follow its import to the canonical
subfamily before changing behavior. Use `governance/charter.py` to confirm the
eight permitted ownership families and identify logic that belongs in runtime,
knowledge, intelligence, or lab instead.

## Trace one result backwards

Begin at the rendered workflow report or table, identify its typed report,
follow referenced claims and provenance into interpretation or quantification,
then continue to identification and imported source rows. Inspect the study
design and policy objects at each transformation. This backwards route exposes
loss, ambiguity, thresholds, and rejected evidence that a top-level command
alone cannot explain.
