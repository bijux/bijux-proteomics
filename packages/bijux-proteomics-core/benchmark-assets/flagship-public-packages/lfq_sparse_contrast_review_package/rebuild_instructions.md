# Rebuild LFQ Companion Package

Asset root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package`

Rebuild discipline:

- refresh copied snapshots from the tracked upstream repo paths in `source_locator_manifest.json`
- rerun the workflow generalization asset refresh command to regenerate package metadata and reports

Command:

```bash
uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh
```

Expected wall time: `3` minutes
Expected disk footprint: `6` MB
