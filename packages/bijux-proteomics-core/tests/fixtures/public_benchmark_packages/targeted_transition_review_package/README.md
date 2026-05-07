# Targeted Transition Review Package

This package is the outsider-readable targeted benchmark center for the current
repository proof. It keeps transition-level QC, approved follow-up, failed
follow-up, and refused follow-up visible together.

Tracked package evidence:

- one targeted QC table in
  `packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv`
- one approved follow-up packet in
  `packages/bijux-proteomics-lab/tests/fixtures/handoffs/supported_targeted_follow_up.json`
- one failed follow-up packet in
  `packages/bijux-proteomics-lab/tests/fixtures/handoffs/failed_targeted_transition_follow_up.json`
- one refused follow-up packet in
  `packages/bijux-proteomics-lab/tests/fixtures/handoffs/refused_targeted_follow_up.json`

Tracked package metadata lives beside this file:

- `package_manifest.json`
- `artifact_inventory.json`
- `quality_sheet.json`
- `lifecycle.json`

What this package can support:

- bounded targeted transition review with explicit control and interference
  caution
- visible operator consequence packets for approved, failed, and refused cases

What this package does not support:

- flagship runtime execution yet
- vendor chromatogram parity
- decision-grade targeted claims without stronger calibration and comparator
  proof
