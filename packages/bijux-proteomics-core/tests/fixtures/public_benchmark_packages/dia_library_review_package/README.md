# DIA Library Review Package

This package is the outsider-readable DIA benchmark center for the current
repository proof. It keeps the public DIA story anchored in tracked exported
results and explicit library assumptions instead of loose capability prose.

Tracked package evidence:

- one Spectronaut-style report in
  `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv`
- one Spectronaut-style pipeline export in
  `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_pipeline_export.tsv`
- one Spectronaut-style settings snapshot in
  `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_settings.txt`
- one DIA-NN-style pipeline export in
  `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv`
- one DIA-NN-style configuration snapshot in
  `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_config.json`

Tracked package metadata lives beside this file:

- `package_manifest.json`
- `artifact_inventory.json`
- `quality_sheet.json`
- `lifecycle.json`

What this package can support:

- bounded DIA extraction review with explicit library-conditioned assumptions
- explicit confrontation between Spectronaut-style and DIA-NN-style export
  surfaces
- clear refusal of chromatogram-level vendor parity claims

What this package does not support:

- live Spectronaut or DIA-NN execution inside the repository
- chromatogram-level vendor tuning parity
- broad protein-level absence claims beyond the tracked library-conditioned
  export scope
