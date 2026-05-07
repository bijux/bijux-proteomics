# PTM Localization Review Package

This package is the outsider-readable PTM benchmark center for the current
repository proof. It keeps localization evidence, occupancy-facing features,
raw-spectrum context, and sequence context together.

Tracked package evidence:

- one PTM localization table in
  `packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv`
- one PTM feature table in
  `packages/bijux-proteomics-core/tests/fixtures/ptm/ptm_features.tsv`
- one reference FASTA in
  `packages/bijux-proteomics-core/tests/fixtures/fasta/ptm_sites.fasta`
- one raw-like spectrum in
  `packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf`

Tracked package metadata lives beside this file:

- `package_manifest.json`
- `artifact_inventory.json`
- `quality_sheet.json`
- `lifecycle.json`

What this package can support:

- bounded PTM localization review with explicit ambiguity
- explicit occupancy and targetability caution

What this package does not support:

- flagship runtime execution yet
- broad PTM-family parity claims
- comparator-backed decision-grade PTM support
