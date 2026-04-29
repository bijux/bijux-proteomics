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

## Interpretation boundaries

This is a serious reusable inference layer, but it is still intentionally
bounded.

It does not yet claim:

- picked-group FDR across indistinguishable protein groups
- alternative inference strategies beyond the current greedy parsimony policy
- protein-level competition models tuned to specific upstream engines
- operator-facing HTML reports or interactive coverage views
