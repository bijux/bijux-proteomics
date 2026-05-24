# Targeted Transition Review Package

This package is the outsider-readable targeted benchmark center for the current
repository proof. It keeps a runnable Skyline-style transition result table,
replicate design, transition-level QC, approved follow-up, failed follow-up,
and refused follow-up visible together.

Tracked package evidence:

- one Skyline-style targeted result table in
  `evidence/skyline_targeted_qc_results.tsv`
- one targeted replicate design in
  `evidence/skyline_targeted_qc.design.tsv`
- one targeted QC table in
  `evidence/targeted_benchmark_qc.tsv`
- one approved follow-up packet in
  `follow_up/supported_targeted_follow_up.json`
- one failed follow-up packet in
  `follow_up/failed_targeted_transition_follow_up.json`
- one refused follow-up packet in
  `follow_up/refused_targeted_follow_up.json`

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

- bounded targeted transition review with explicit control, interference,
  coelution, fragment-ratio, and replicate-CV caution
- visible operator consequence packets for approved, failed, and refused cases

What this package does not support:

- vendor chromatogram parity
- absolute calibration claims
- decision-grade targeted claims without stronger calibration and comparator
  proof

This asset root is product-owned. The exact copied-source provenance is in
`source_locator_manifest.json`, the scientific references are in
`citation_manifest.json`, the copied-versus-generated boundary is in
`generated_boundary.json`, and the maintainer rebuild command is in
`rebuild_instructions.md`.
