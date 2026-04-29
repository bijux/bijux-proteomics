# First Useful Proteomics Run

This package now supports a minimal but real proteomics path from source
sequence input to thresholded identifications and spectrum annotation.

The checked fixture pack lives in
`packages/bijux-proteomics-core/tests/fixtures/first_useful_run/` and contains:

- `proteins.fasta`
- `results.tsv`
- `spectra.mgf`
- `fixture_manifest.json`

## Inputs

- FASTA: canonical protein sequence input
- TSV: search-engine-like peptide-spectrum matches
- MGF: observed tandem mass spectrum

## Validate the inputs

```bash
bijux-proteomics validate proteins.fasta --kind fasta
bijux-proteomics validate results.tsv --kind psm
bijux-proteomics validate spectra.mgf --kind mgf
```

## Summarize what is in the files

```bash
bijux-proteomics summarize proteins.fasta --kind fasta
bijux-proteomics summarize results.tsv --kind psm
bijux-proteomics summarize spectra.mgf --kind mgf
```

## Digest the proteins

```bash
bijux-proteomics digest proteins.fasta \
  --protease trypsin \
  --digestion-mode full \
  --format jsonl \
  --out peptides.jsonl \
  --manifest-out digest.manifest.json
```

## Filter identifications by basic target-decoy FDR

```bash
bijux-proteomics fdr results.tsv \
  --decoy-prefix DECOY_ \
  --threshold 0.50 \
  --jsonl-out accepted.jsonl \
  --provenance-out fdr.provenance.json
```

The fixture set is intentionally tiny. The threshold is loose because the goal
here is a reproducible contract example, not a biologically meaningful cutoff.

## Inspect and annotate the matched spectrum

```bash
bijux-proteomics spectrum-stats spectra.mgf --provenance-out spectra.provenance.json

bijux-proteomics spectrum-annotate spectra.mgf \
  --peptide PEPTIDEK \
  --tsv-out annotation.tsv \
  --plot-out plot.json
```

This produces:

- a spectrum collection summary
- a provenance manifest for the MGF input
- fragment-ion annotations in TSV form
- a stable plot payload for downstream rendering

## What this walkthrough proves

- FASTA intake is parseable and validated
- protease digestion is reproducible
- search-result TSV intake is normalized into stable PSM records
- basic target-decoy filtering works on the normalized records
- observed spectrum data can be annotated against the accepted peptide

## What it does not claim

- production-calibrated FDR
- mzML ingestion
- search-engine-specific rescoring
- full protein inference
- quantitative analysis
