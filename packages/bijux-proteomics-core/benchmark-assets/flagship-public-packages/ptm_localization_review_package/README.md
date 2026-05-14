# PTM Localization Review Package

This package is the outsider-readable PTM benchmark center for the current
repository proof. It keeps localization evidence, occupancy-facing features,
raw-spectrum context, and sequence context together.

Tracked package evidence:

- one PTM localization table in
  `evidence/localization_results.tsv`
- one PTM feature table in
  `evidence/ptm_features.tsv`
- one reference FASTA in
  `evidence/ptm_sites.fasta`
- one raw-like spectrum in
  `evidence/spectra.mgf`

Tracked package metadata lives beside this file:

- `source_locator_manifest.json`
- `citation_manifest.json`
- `generated_boundary.json`
- `rebuild_instructions.md`
- `package_manifest.json`
- `artifact_inventory.json`
- `quality_sheet.json`
- `lifecycle.json`

What this package can support:

- bounded PTM localization review with explicit ambiguity
- explicit occupancy and targetability caution

What this package does not support:

- broad PTM-family parity claims
- comparator-backed decision-grade PTM support

This asset root is product-owned. The exact copied-source provenance is in
`source_locator_manifest.json`, the scientific references are in
`citation_manifest.json`, the copied-versus-generated boundary is in
`generated_boundary.json`, and the maintainer rebuild command is in
`rebuild_instructions.md`.
