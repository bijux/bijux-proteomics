# Provider Ownership

This dossier records the canonical owner modules for runtime provider binding
and provider execution support.

## Provider boundary rule

`providers/` owns provider binding, capability checks, install hints,
metadata, and runtime-facing execution support. Lower packages should not
recreate these rules.

## Base provider contracts

- owner code: `src/bijux_proteomics_runtime/providers/base.py`, `src/bijux_proteomics_runtime/providers/errors.py`
- owner tests: `tests/test_runtime_provider_surface.py`
- owner fixtures: `tests/conftest.py`
- contract: provider protocol, metadata, result envelopes, and runtime install-hint failures stay pinned to runtime

## Capability and factory gates

- owner code: `src/bijux_proteomics_runtime/providers/capabilities.py`, `src/bijux_proteomics_runtime/providers/factory.py`, `src/bijux_proteomics_runtime/providers/support.py`
- owner tests: `tests/test_provider_capability_validation.py`, `tests/test_provider_capability_registry_surface.py`, `tests/test_runtime_provider_surface.py`
- owner fixtures: `tests/fixtures/execution/sequence_review_path.json`, `tests/fixtures/execution/container_review_path.json`
- contract: runtime decides whether a requested provider and execution mode combination is supported before orchestration proceeds

## Heuristic provider baseline

- owner code: `src/bijux_proteomics_runtime/providers/heuristic.py`
- owner tests: `tests/test_runtime_provider_surface.py`
- owner fixtures: `tests/conftest.py`
- contract: heuristic provider remains the baseline runtime-owned fallback surface

## Local provider bindings

- owner code: `src/bijux_proteomics_runtime/providers/local/esmfold.py`, `src/bijux_proteomics_runtime/providers/local/rosettafold.py`
- owner tests: `tests/test_runtime_provider_surface.py`, `tests/test_runtime_execution_conformance.py`
- owner fixtures: `tests/fixtures/execution/sequence_review_path.json`
- contract: local provider install hints and execution hooks stay grouped under runtime-owned local bindings

## Experimental API providers

- owner code: `src/bijux_proteomics_runtime/providers/experimental/colabfold.py`, `src/bijux_proteomics_runtime/providers/experimental/openprotein.py`, `src/bijux_proteomics_runtime/providers/experimental/_async_utils.py`
- owner tests: `tests/test_runtime_provider_surface.py`
- owner fixtures: `tests/conftest.py`
- contract: experimental remote-provider support stays explicit and does not widen the stable provider contract surface by accident
