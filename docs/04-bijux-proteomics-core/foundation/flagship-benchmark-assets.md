---
title: Flagship Benchmark Assets
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-07
---

# Flagship Benchmark Assets

The flagship benchmark packages are no longer treated like disposable test
fixtures. They live under one product-owned root:

`packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/`

The punishing companion surface now lives beside them under:

`packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/`

This handbook explains what is copied, what is generated, what public sources
justify the copied files, how to rebuild the package metadata, and where the
repository keeps the current freshness and obsolescence pressure visible.

The direct audit and lineage follow-up pages are:

- [Benchmark Asset Audit](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-asset-audit/)
- [Benchmark Licensing and Redistribution](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-licensing-and-redistribution/)
- [Benchmark Incompleteness Ledger](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-incompleteness-ledger/)
- [Benchmark Flagship Status](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-flagship-status/)
- [DDA Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dda-benchmark-lineage/)
- [DIA Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dia-benchmark-lineage/)
- [LFQ Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/lfq-benchmark-lineage/)
- [Multiplex Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/multiplex-benchmark-lineage/)
- [PTM Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ptm-benchmark-lineage/)
- [Targeted Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/targeted-benchmark-lineage/)

## What Exists Per Package

Each flagship package root now carries:

- copied evidence snapshots or follow-up packets that the benchmark actually
  reviews
- `source_locator_manifest.json`
- `citation_manifest.json`
- `generated_boundary.json`
- `rebuild_instructions.md`
- `package_manifest.json`
- `artifact_inventory.json`
- `quality_sheet.json`
- `lifecycle.json`

The DDA package also carries:

- `scientific_invariants.json`
- `warning_demonstrations.json`

## Shared Asset Governance Files

The root-level support files are:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/asset_root_contract.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/freshness_report.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/obsolescence_audit.json`

Use them for different questions:

- `asset_root_contract.json`: what each package root must contain and why it is
  allowed to exist
- `freshness_report.json`: whether the copied snapshots are still present and
  whether the public source pages are still reachable
- `obsolescence_audit.json`: whether the package is still scientifically too
  weak to count as a stable end state

## How To Rebuild

When copied evidence, package metadata, or root-level reports need to be
refreshed, run:

```bash
uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh
```

That command rewrites:

- the shared asset-root contract
- the freshness report
- the obsolescence audit
- each package root's source locator manifest
- each package root's citation manifest
- each package root's generated-boundary manifest
- each package root's rebuild instructions
- each package root's package manifest, artifact inventory, quality sheet, and
  lifecycle record

## Current Scientific Limits

These package roots are stronger than the old fixture-only posture, but they do
not yet close the scientific gap across all workflow families.

- `dda`: outsider-auditable, but still built around imported-result snapshots
  instead of live in-repo search reruns
- `dia`: publicly inspectable, but still library-conditioned and import-backed
- `lfq`: runtime-backed, but still blocked on stronger comparator and
  generalization proof
- `multiplex`: runtime-backed, but still thin on lab consequence and broader
  authority
- `ptm`: runtime-backed, but still blocked on stronger comparator and PTM-family
  breadth
- `targeted`: public and consequence-bearing, but still import-only and not yet
  calibration-strong enough for decision-grade trust

Those limits are now pressure-tested explicitly through the blinded holdout and
perturbation roots in the Flagship Challenge Corpus Catalog.

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics/benchmarks/flagship_asset_roots.py`
- `packages/bijux-proteomics-core/src/bijux_proteomics/benchmarks/flagship_asset_maintenance.py`
- `packages/bijux-proteomics-core/tests/benchmarks/test_flagship_asset_root_surface.py`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages`

## Challenge Pressure

Open [Flagship Challenge Corpus Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-challenge-corpus-catalog/)
when you need the frozen holdouts and adversarial perturbations that challenge
these public package claims directly.
