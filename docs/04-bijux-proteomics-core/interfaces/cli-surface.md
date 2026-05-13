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
- `fasta-contaminants`
- `fasta-profile`
- `fasta-stats`
- `fasta-dedup`
- `fasta-filter`
- `fasta-provenance`
- `fasta-decoy`
- `target-decoy-validate`
- `peptide-index`
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

`fasta-profile` emits a richer database-review object with:

- a summary block covering input records, accepted proteins, rejected records,
  unique accessions, target count, decoy count, contaminant count, total
  residues, length extremes, and organism annotation coverage
- a stable length-distribution ledger across the bins `1-99`, `100-249`,
  `250-499`, `500-999`, and `1000+`
- an organism-distribution ledger when organism evidence is present in the
  accepted records

`fasta-profile` also supports reviewer-facing TSV exports through:

- `--summary-tsv-out`
- `--length-tsv-out`
- `--organism-tsv-out`

`fasta-contaminants` builds a more realistic search database by:

- appending the owned built-in contaminant panel unless `--no-include-builtin`
  is selected
- appending one or more user-provided contaminant FASTA files through repeated
  `--contaminant-fasta`
- relabeling appended contaminant proteins with the stable `CON__` prefix
- writing a build report with separate built-in and external append counts plus
  skipped duplicate contaminant accessions

`fasta-decoy` builds a target-decoy database and reports both accession-level
and sequence-level review signals.

- `--decoy-mode reverse` and `--decoy-mode shuffle` select the owned decoy
  construction method.
- `--prefix` preserves target protein identity inside the decoy accession while
  enforcing collision-free accession generation.
- Mixed target-plus-decoy inputs are rejected instead of being re-expanded.
- Prefix choices that would collide with existing target accessions fail before
  output is written.

The `fasta-decoy` JSON payload includes:

- `mode`
- `prefix`
- `seed`
- `output_fasta`
- `target_count`
- `decoy_count`
- `report`
- `generation_report`
- `output_sha256`
- `reproducibility_hash`

`generation_report` adds reviewer-facing target-decoy construction details:

- input target count
- generated decoy count
- unchanged sequence count and accession list
- target-sequence collision count and accession list
- validity flag for the generated decoy surface

`target-decoy-validate` checks a finished database after generation and reports:

- target and decoy counts
- prefix and mode compatibility
- duplicate accession and duplicate sequence burden
- target-versus-decoy sequence overlap signals
- overall validity of the target-decoy database

`peptide-index` digests a FASTA database and reports how one or more peptide
queries map back to proteins under the selected digestion assumptions.

- `--peptide` is repeatable and accepts plain or modified peptide notation.
- `--protease`, `--missed-cleavages`, and `--digestion-mode` define the digest
  policy used to build the searchable peptide space.
- `--il-equivalent` optionally collapses isoleucine and leucine during lookup.
- `--protein-group-map` accepts a TSV with `accession` and `protein_group`
  columns so group-specific peptides stay explicit.

The `peptide-index` JSON payload includes:

- input record count
- query peptide count
- protease
- digestion mode
- missed cleavages
- I/L-equivalence flag
- protein-group-map presence flag
- one report object with per-peptide lookup entries and summary counts

Each lookup entry reports:

- the original query peptide
- the canonical residue sequence used for lookup
- the final lookup sequence after optional I/L normalization
- whether modification stripping or I/L-equivalent lookup was applied
- matched protein accessions, families, and groups
- protein-group count
- uniqueness and audit class when the peptide is present
- target, decoy, contaminant, mixed, or missing database membership
- missed-cleavage counts observed among the matching peptide instances
- a reviewer-facing explanation string

`fasta-stats` reports FASTA-wide review metrics such as duplicate accession
count, duplicate sequence count, target count, decoy count, contaminant count,
and sequence-length summary values.

`summarize --kind fasta` returns the higher-level FASTA summary, the parser-level
database composition, and the richer FASTA profile so operators can distinguish
structural file quality from biological database makeup and annotation burden.

For PSM evidence, the contaminant-review surface is:

- `psm-contaminants`

`psm-contaminants` emits a separate contaminant-match report with:

- contaminant PSM count
- pure-contaminant versus mixed-reference PSM counts
- contaminant peptide count
- contaminant protein counts
- row-level entries listing contaminant and target protein references for each
  contaminant-carrying match

`summarize --kind psm` now includes the same contaminant report alongside the
standard PSM, peptide, and protein summaries.
