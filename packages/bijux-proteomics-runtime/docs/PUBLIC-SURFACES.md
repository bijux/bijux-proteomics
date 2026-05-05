# Public Surfaces

This dossier records the canonical public runtime surfaces and the owner paths
that defend them.

## Package-root stable entrypoints

The package root stays stable for external callers, but each public surface has
an exact owner module that runtime maintainers should edit directly.

## `interfaces.cli:cli`

- owner code: `src/bijux_proteomics_runtime/interfaces/cli.py`
- owner tests: `tests/test_runtime_cli_surface.py`, `tests/test_runtime_interfaces.py`
- owner fixtures: `tests/fixtures/execution/sequence_review_path.json`
- contract: CLI remains the canonical operator entrypoint for run, import, inspect, compare, resume, and API serving

## `api.app:create_app`

- owner code: `src/bijux_proteomics_runtime/api/app.py`, `src/bijux_proteomics_runtime/api/v1/router.py`
- owner tests: `tests/test_runtime_api_surface.py`, `tests/test_runtime_api_fixtures.py`
- owner fixtures: `tests/fixtures/api/runtime_health_response.json`, `tests/fixtures/api/runtime_status_response.json`
- contract: FastAPI assembly, health surfaces, readiness, and v1 router inclusion stay pinned to runtime-owned wiring

## `runs.manager:RunManager`

- owner code: `src/bijux_proteomics_runtime/runs/manager.py`, `src/bijux_proteomics_runtime/runs/operations.py`
- owner tests: `tests/test_runtime_execution_surface.py`, `tests/test_runtime_execution_conformance.py`
- owner fixtures: `tests/fixtures/execution/sequence_review_path.json`, `tests/fixtures/execution/container_review_path.json`
- contract: runtime execution coordination remains in `runs/` rather than being rebuilt in interfaces, compat, or downstream packages

## `workflows.paths:run_reviewable_sequence_path`

- owner code: `src/bijux_proteomics_runtime/workflows/paths.py`
- owner tests: `tests/test_runtime_workflow_paths.py`, `tests/test_runtime_local_and_import_end_to_end.py`
- owner fixtures: `tests/fixtures/execution/sequence_review_path.json`
- contract: canonical sequence-to-review execution keeps publishing a runtime-owned manifest and replay-safe artifacts

## `workflows.paths:run_reviewable_import_path`

- owner code: `src/bijux_proteomics_runtime/workflows/paths.py`, `src/bijux_proteomics_runtime/runs/import_lineage.py`
- owner tests: `tests/test_runtime_workflow_paths.py`, `tests/test_runtime_local_and_import_end_to_end.py`, `tests/test_runtime_import_surface.py`
- owner fixtures: `tests/fixtures/execution/import_review_path.json`
- contract: canonical import-to-review execution keeps imported evidence separate from runtime-derived review outputs
