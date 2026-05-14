# PTM Workflows

`bijux-proteomics-core` now includes a first-class PTM localization and site
aggregation surface for operator-facing phosphosite-style analysis.

## What it covers

- localized PTM evidence parsing from search-style TSV tables
- peptide-to-protein site mapping against strict FASTA inputs
- aggregated PTM site tables with ambiguity state
- site-level coverage and target-decoy FDR summaries
- motif-window extraction and enrichment-list export
- optional occupancy estimation from MS1 feature tables

## Input contract

The PTM evidence parser expects a delimited table with these canonical columns:

- `spectrum_id`
- `peptide`
- `charge`
- `score`
- `proteins`
- `localization_score`

Optional columns:

- `sample_id`
- `q_value`
- `candidate_sites`
- `decoy_label`

`candidate_sites` is interpreted as peptide-relative one-based positions for
the modified residue candidates reported by the upstream engine.

## Core workflow

```bash
bijux-proteomics ptm summarize localization_results.tsv proteins.fasta \
  --features ptm_features.tsv \
  --threshold 0.1 \
  --flank-size 3 \
  --out ptm.report.json
```

The payload includes:

- `site_table`
- `ambiguity_report`
- `coverage_report`
- `fdr_report`
- `motif_windows`
- `enrichment_input`
- `occupancy` when a feature table is provided

## Python API

```python
from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_enrichment_input,
    build_ptm_motif_windows,
    build_ptm_site_ambiguity_report,
    build_ptm_site_coverage_report,
    build_ptm_site_fdr,
    build_ptm_site_table,
    estimate_ptm_site_occupancy,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document

evidence = parse_ptm_localization_tsv(Path("localization_results.tsv"))
fasta_report = parse_fasta_document(Path("proteins.fasta").read_text(), mode=FastaParseMode.STRICT)
protein_sequences = {
    record.canonical_accession: record.residues
    for record in fasta_report.accepted_records
}
mappings = map_ptm_evidence_to_protein_sites(
    evidence.accepted_records,
    protein_sequences=protein_sequences,
)
site_table = build_ptm_site_table(mappings)
ambiguity = build_ptm_site_ambiguity_report(site_table)
coverage = build_ptm_site_coverage_report(mappings)
fdr = build_ptm_site_fdr(site_table, threshold=0.05)
motifs = build_ptm_motif_windows(site_table, protein_sequences=protein_sequences, flank_size=7)
enrichment = build_ptm_enrichment_input(site_table, protein_sequences=protein_sequences)
feature_report = parse_ms1_feature_table(Path("ptm_features.tsv"))
occupancy = estimate_ptm_site_occupancy(site_table, feature_records=feature_report.accepted_records)
```

## Interpretation boundaries

This slice is serious and reusable, but it is still bounded.

It does not yet claim:

- site-localization rescoring from raw spectra
- peptide/protein competition models beyond the current site-level target-decoy view
- motif enrichment statistics beyond stable site/background export
- probabilistic occupancy models or batch-aware PTM differential analysis
