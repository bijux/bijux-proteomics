# Rebuild TARGETED Flagship Asset Root

Asset root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`

Rebuild discipline:

- refresh copied snapshots from the tracked upstream repo paths in `source_locator_manifest.json`
- rerun the flagship asset maintenance command to regenerate package metadata and reports
- confirm the shared freshness report and obsolescence audit still match the rebuilt package

Command:

```bash
uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh
```

Expected wall time: `5` minutes
Expected disk footprint: `4` MB
