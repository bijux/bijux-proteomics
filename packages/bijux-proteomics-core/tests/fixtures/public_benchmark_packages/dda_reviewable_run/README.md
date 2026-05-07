# DDA Reviewable Public Package

This package is the outsider-readable DDA benchmark center for the current
repository proof. It replaces the older DDA toy surface with tracked files
that a reviewer can open directly:

- raw-like tandem spectra in
  `packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf`
- one primary imported MaxQuant pipeline export in
  `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv`
- one comparator MSFragger pipeline export in
  `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv`
- pinned search settings for both engine families
- one experimental design table and one workflow expectation manifest

Tracked package metadata lives beside this file:

- `package_manifest.json`
- `artifact_inventory.json`
- `quality_sheet.json`
- `lifecycle.json`
- `scientific_invariants.json`
- `warning_demonstrations.json`

What this package can support:

- bounded peptide-facing DDA review with explicit target-decoy visibility
- bounded imported-result review with visible search settings and raw-like
  spectra identity
- explicit cross-engine warning pressure at the protein rollup layer

What this package does not support:

- in-repo live-engine rerun parity
- broad production-scale DDA claims beyond the tracked exported-result scope
- protein-level certainty that outruns the demonstrated cross-engine drift

Key scientific references:

- target-decoy confidence boundary:
  `10.1038/nmeth1019` and
  `https://www.nature.com/articles/nmeth1019`
- protein inference caution:
  `10.1074/mcp.R111.014795` and
  `https://pmc.ncbi.nlm.nih.gov/articles/PMC3494198/`
- reference proteome grounding:
  `10.1093/nar/gkae1010` and
  `https://www.uniprot.org`
