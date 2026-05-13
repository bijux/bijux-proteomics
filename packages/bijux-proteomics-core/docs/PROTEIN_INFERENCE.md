# Protein Inference

`bijux-proteomics-core` now includes a first-class protein inference surface on
top of normalized PSM evidence.

## What it covers

- separate PSM, peptide, and protein FDR views
- grouped FDR over charge state and modification state
- indistinguishable protein grouping
- greedy parsimony protein selection
- razor peptide assignment
- picked target-decoy protein FDR
- confidence labels with explicit explanations
- optional FASTA-backed coverage and peptide uniqueness checks
- direct sequence-backed protein coverage review through `protein-coverage`
- plot-ready sequence-backed coverage payloads through `protein-coverage-plot`

## Core workflow

```bash
bijux-proteomics infer-proteins results.tsv \
  --threshold 0.05 \
  --fasta proteins.fasta
```

The payload includes:

- `level_fdr`
- `grouped_fdr`
- `protein_groups`
- `parsimony_proteins`
- `picked_protein_fdr`
- `confidence_labels`
- `razor_assignments`
- `protein_coverage` when FASTA is supplied
- `database_uniqueness` when FASTA is supplied

For direct sequence review outside the broader inference payload:

```bash
bijux-proteomics protein-coverage results.tsv \
  --threshold 0.05 \
  --fasta proteins.fasta
```

That coverage surface emits:

- a compact summary over sequence-backed coverage
- one reviewer-facing protein row per observed protein with covered regions,
  unique/shared peptides, and unmatched-peptide visibility
- one region ledger that keeps each contiguous covered interval explicit

For static sequence-backed coverage visualizations:

```bash
bijux-proteomics protein-coverage-plot results.tsv \
  --threshold 0.05 \
  --fasta proteins.fasta \
  --positions-tsv-out protein-coverage.positions.tsv \
  --svg-out protein-coverage.svg \
  --html-out protein-coverage.html
```

That plot surface emits:

- one plot-ready track per protein with explicit peptide start/end positions
- preserved modified-peptide notation, peptide confidence, and optional
  intensity when the source evidence carries them
- one positional TSV ledger plus static SVG and HTML outputs for operator review

## Interpretation boundaries

This is a serious reusable inference layer, but it is still intentionally
bounded.

It does not yet claim:

- picked-group FDR across indistinguishable protein groups
- alternative inference strategies beyond the current greedy parsimony policy
- protein-level competition models tuned to specific upstream engines
- interactive coverage views
