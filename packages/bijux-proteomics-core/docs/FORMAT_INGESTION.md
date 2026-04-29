# Format Ingestion And Run Bundles

`bijux-proteomics-core` now supports a normalized ingestion path for:

- MGF
- mzML
- generic search-result TSV
- experimental design TSV or CSV
- modification registries

## mzML intake

The mzML surface parses tandem spectra into the same `SpectrumModel` contract
used by the existing MGF path.

It also extracts stable run metadata:

- run identifier
- acquisition start time
- instrument configuration ids
- instrument names
- accepted and rejected spectrum counts

Binary arrays are validated before a spectrum is accepted:

- required m/z and intensity arrays
- consistent array lengths
- `defaultArrayLength` agreement
- valid base64 payload width

Use the CLI to validate or summarize mzML input:

```bash
bijux-proteomics validate run.mzml --kind mzml
bijux-proteomics summarize run.mzml --kind mzml
```

## Experimental design tables

The design-table parser normalizes rows with these required columns:

- `sample_id`
- `condition`
- `replicate`
- `fraction`
- `spectra_file`

Optional columns:

- `identifications_file`
- `instrument`
- `search_engine`

Validate or summarize a design table:

```bash
bijux-proteomics validate experiment.design.tsv --kind design-table
bijux-proteomics summarize experiment.design.tsv --kind design-table
```

## Format conversion

The conversion surface writes normalized Bijux outputs:

```bash
bijux-proteomics format-convert run.mzml \
  --kind mzml \
  --to mgf \
  --out run.converted.mgf

bijux-proteomics format-convert run.mzml \
  --kind mzml \
  --to spectra-jsonl \
  --out spectra.jsonl
```

Supported targets:

- `mgf`
- `spectra-jsonl`
- `psm-jsonl`
- `design-jsonl`

## Normalized run bundles

The run-bundle surface materializes one directory that carries:

- normalized spectra
- normalized identifications
- harmonized run metadata
- validation and provenance artifacts

```bash
bijux-proteomics bundle-run \
  --spectra run.mzml \
  --identifications results.tsv \
  --design experiment.design.tsv \
  --out-dir bundle
```

The bundle directory includes:

- `spectra.normalized.mgf`
- `spectra.validation.json`
- `identifications.normalized.jsonl`
- `identifications.summary.json`
- `design.normalized.jsonl`
- `run.metadata.json`
- `bundle.manifest.json`

## What this surface does not claim

- full mzML vendor-dialect coverage
- mzIdentML, mzTab, pepXML, or idXML ingestion
- quantitative feature parsing
- production-scale benchmark claims beyond streaming parser structure
