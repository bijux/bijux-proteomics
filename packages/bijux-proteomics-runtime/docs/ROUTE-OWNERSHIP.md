# Route Ownership

This dossier records the canonical owner modules for runtime HTTP route
surfaces.

## Route assembly rule

`api/routes/` owns route contracts. `api/v1/endpoints/` owns the FastAPI
endpoint wiring that calls those contracts. Runtime should not recreate these
surfaces in broad route wrappers.

## `runtime_execution`

- owner code: `src/bijux_proteomics_runtime/api/routes/runtime_execution.py`
- endpoint wiring: `src/bijux_proteomics_runtime/api/v1/endpoints/run.py`, `src/bijux_proteomics_runtime/api/v1/endpoints/external_import.py`, `src/bijux_proteomics_runtime/api/v1/endpoints/resume.py`, `src/bijux_proteomics_runtime/api/v1/endpoints/inspect.py`, `src/bijux_proteomics_runtime/api/v1/endpoints/compare.py`
- owner tests: `tests/test_runtime_execution_route_surface.py`, `tests/test_runtime_api_surface.py`
- owner fixtures: `tests/fixtures/api/run_history_response.json`, `tests/runtime_fixture_data.py`

## `review_packets`

- owner code: `src/bijux_proteomics_runtime/api/routes/review_packets.py`
- endpoint wiring: `src/bijux_proteomics_runtime/api/v1/endpoints/runtime_contracts.py`
- owner tests: `tests/test_review_packet_route_surface.py`
- owner fixtures: `tests/runtime_fixture_data.py`

## `quant_reports`

- owner code: `src/bijux_proteomics_runtime/api/routes/quant_reports.py`
- endpoint wiring: `src/bijux_proteomics_runtime/api/v1/endpoints/runtime_contracts.py`
- owner tests: `tests/test_quant_report_route_surface.py`
- owner fixtures: `tests/runtime_fixture_data.py`

## `ptm_reports`

- owner code: `src/bijux_proteomics_runtime/api/routes/ptm_reports.py`
- endpoint wiring: `src/bijux_proteomics_runtime/api/v1/endpoints/runtime_contracts.py`
- owner tests: `tests/test_ptm_report_route_surface.py`
- owner fixtures: `tests/runtime_fixture_data.py`

## `evidence_graph`

- owner code: `src/bijux_proteomics_runtime/api/routes/evidence_graph.py`
- endpoint wiring: `src/bijux_proteomics_runtime/api/v1/endpoints/runtime_contracts.py`
- owner tests: `tests/test_evidence_graph_query_route_surface.py`
- owner fixtures: `tests/fixtures/api/evidence_lookup_response.json`

## `lab_handoffs`

- owner code: `src/bijux_proteomics_runtime/api/routes/lab_handoffs.py`
- endpoint wiring: `src/bijux_proteomics_runtime/api/v1/endpoints/runtime_contracts.py`
- owner tests: `tests/test_lab_handoff_route_surface.py`
- owner fixtures: `tests/runtime_fixture_data.py`

## `adapter_conformance`

- owner code: `src/bijux_proteomics_runtime/api/routes/adapter_conformance.py`
- endpoint wiring: `src/bijux_proteomics_runtime/api/v1/endpoints/runtime_contracts.py`
- owner tests: `tests/test_adapter_conformance_route_surface.py`
- owner fixtures: `tests/runtime_fixture_data.py`
