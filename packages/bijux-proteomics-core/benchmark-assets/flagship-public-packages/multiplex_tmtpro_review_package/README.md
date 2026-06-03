# Multiplex TMTpro Review Package

This package is the outsider-readable multiplex benchmark center for the
current repository proof. It keeps reporter-channel evidence, pooled-reference
and bridge-channel roles, interference pressure, and chemistry caveats visible
together.

Tracked package evidence:

- one TMT reporter-ion table in
  `evidence/tmt_reporter_table.tsv`
- one retained channel-level feature snapshot in
  `evidence/multiplex_ms1_features.tsv`
- one multiplex design table in
  `evidence/multiplex.design.tsv`

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

- bounded TMTpro reporter-channel review
- explicit missing-channel, interference, imbalance, and reference-channel caveats
- runnable channel QC, normalization, ratio, differential, and report benchmarks

What this package does not support:

- label-free-style abundance interpretation
- broad vendor-specific multiplex parity claims

This asset root is product-owned. The exact copied-source provenance is in
`source_locator_manifest.json`, the scientific references are in
`citation_manifest.json`, the copied-versus-generated boundary is in
`generated_boundary.json`, and the maintainer rebuild command is in
`rebuild_instructions.md`.
