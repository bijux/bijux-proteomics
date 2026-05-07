# LFQ Cohort Review Package

This package is the outsider-readable LFQ benchmark center for the current
repository proof. It keeps study-scale feature evidence and cohort-shaped
design metadata visible together instead of hiding them behind tidy matrix
language.

Tracked package evidence:

- one study-scale LFQ feature table in
  `evidence/study_scale_ms1_features.tsv`
- one cohort-shaped design table in
  `evidence/study_scale.design.tsv`
- one bounded reproducibility ledger in
  `evidence/quant_reproducibility_manifest.json`

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

- bounded LFQ repeatability review with explicit missingness and cohort-design
  semantics
- visible batch and replicate structure instead of flattened abundance tables

What this package does not support:

- decision-grade abundance claims
- broad cohort transfer or spike-in accuracy claims

This asset root is product-owned. The exact copied-source provenance is in
`source_locator_manifest.json`, the scientific references are in
`citation_manifest.json`, the copied-versus-generated boundary is in
`generated_boundary.json`, and the maintainer rebuild command is in
`rebuild_instructions.md`.
