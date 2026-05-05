# Artifact Lineage

This dossier records the owner modules that keep runtime artifacts replay-safe,
reviewable, and provenance-aware.

## Lineage rule

Runtime must keep imported evidence, runtime-derived outputs, replay bundles,
and retention classes explicit. Downstream packages should not infer lineage by
parsing private workspace layout.

## Run context and artifact policy

- owner code: `src/bijux_proteomics_runtime/runs/contracts.py`, `src/bijux_proteomics_runtime/runtime/workspace.py`
- owner tests: `tests/runtime/test_runtime_context_contracts.py`, `tests/api/test_runtime_transport_contracts.py`
- owner fixtures: `tests/fixtures/execution/sequence_review_path.json`
- contract: run identity, dataset identity, environment identity, and retention classes remain machine-readable

## Artifact ledger and retention refresh

- owner code: `src/bijux_proteomics_runtime/runs/ledger.py`, `src/bijux_proteomics_runtime/runs/artifacts.py`
- owner tests: `tests/runs/test_runtime_artifact_ledger.py`, `tests/runs/test_runtime_integrity_surface.py`
- owner fixtures: `tests/fixtures/execution/cache_claim_safety.json`
- contract: runtime artifact inventories keep hashes, producers, sizes, and retention classes reviewable

## Import provenance and derived outputs

- owner code: `src/bijux_proteomics_runtime/runs/import_lineage.py`
- owner tests: `tests/runs/test_runtime_import_surface.py`, `tests/runs/test_runtime_local_and_import_end_to_end.py`
- owner fixtures: `tests/fixtures/execution/import_review_path.json`
- contract: imported evidence stays separate from runtime-derived review documents and import bundles

## Replay bundles, integrity, and rerun boundaries

- owner code: `src/bijux_proteomics_runtime/runs/replay.py`, `src/bijux_proteomics_runtime/runs/integrity.py`, `src/bijux_proteomics_runtime/runs/reruns.py`
- owner tests: `tests/runs/test_runtime_replay_bundle.py`, `tests/runs/test_runtime_replay_integrity_and_cache_end_to_end.py`, `tests/runs/test_runtime_rerun_planning.py`
- owner fixtures: `tests/fixtures/execution/replay_rerun_path.json`, `tests/fixtures/execution/cache_claim_safety.json`
- contract: replay reuse stays explicit, validated, and bounded by dependency and artifact checks

## Launch bundles and reviewable paths

- owner code: `src/bijux_proteomics_runtime/runs/launch_bundles.py`, `src/bijux_proteomics_runtime/workflows/paths.py`
- owner tests: `tests/runs/test_runtime_execution_bundles.py`, `tests/execution/test_runtime_container_and_scheduler_end_to_end.py`, `tests/workflows/test_runtime_workflow_paths.py`
- owner fixtures: `tests/fixtures/execution/container_review_path.json`, `tests/fixtures/execution/scheduler_review_path.json`, `tests/fixtures/execution/sequence_review_path.json`
- contract: local, container, scheduler, and import launch surfaces publish stable review-safe bundles and manifests

## Decision and failure lineage

- owner code: `src/bijux_proteomics_runtime/runs/replay_decisions.py`, `src/bijux_proteomics_runtime/runs/execution_decisions.py`, `src/bijux_proteomics_runtime/runs/failure_reports.py`, `src/bijux_proteomics_runtime/runs/recovery.py`
- owner tests: `tests/runs/test_runtime_replay_decision_reports.py`, `tests/runs/test_runtime_execution_decision_reports.py`, `tests/runs/test_runtime_cleanup_and_recovery.py`, `tests/runs/test_runtime_failure_and_preflight.py`
- owner fixtures: `tests/fixtures/execution/failure_recovery_paths.json`, `tests/fixtures/execution/preflight_failure_cases.json`
- contract: reuse decisions, degraded execution reasons, and recovery-safe failure outputs stay explicit and reviewable
