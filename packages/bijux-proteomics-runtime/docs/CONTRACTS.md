# Contracts

This document captures the public runtime contracts that downstream users and
integrators can rely on at the canonical execution boundary.

## Public package identity

- Distribution name: `bijux-proteomics-runtime`
- Import root: `bijux_proteomics_runtime`
- Canonical CLI command: `bijux-proteomics-runtime`
- Stable entrypoints: `AppConfig`, `RunManager`, `create_app`, and `api.cli:cli`

## Stable contracts

- `bijux_proteomics_runtime.api.cli:cli` is the canonical workflow CLI entrypoint.
- `bijux_proteomics_runtime.api.app:create_app` exposes the canonical FastAPI app constructor.
- `bijux_proteomics_runtime.runs.manager:RunManager` remains the canonical orchestration root.
- `bijux_proteomics_runtime.workflows.paths:run_reviewable_sequence_path` publishes the canonical reviewable sequence-run manifest.
- `bijux_proteomics_runtime.workflows.paths:run_reviewable_import_path` publishes the canonical reviewable import manifest.
- runtime exports typed run context, reviewable outputs, failure reports, and replay artifacts without forcing downstream users to parse private workspaces.

## Exact owner import contracts

- internal and package-maintainer code should import `api.app`, `runs.manager`, `workflows.paths`, `providers.factory`, and `providers.capabilities` directly
- HTTP route ownership is pinned to `api/routes/runtime_execution.py`, `review_packets.py`, `quant_reports.py`, `ptm_reports.py`, `evidence_graph.py`, `lab_handoffs.py`, and `adapter_conformance.py`
- import provenance ownership is pinned to `runs/import_lineage.py`
- preflight, replay-decision, and execution-decision ownership is pinned to `runs/preflight.py`, `runs/replay_decisions.py`, and `runs/execution_decisions.py`

## Supported execution limits

- `execution_mode="auto"` is allowed to degrade to CPU after capability checks
- `execution_mode="cpu"` is supported for CPU-compatible providers only
- `execution_mode="gpu"` is supported only when provider and environment constraints agree
- `launch_surface="container"` and `launch_surface="scheduler"` persist replay-safe launch bundles but do not own container fleet policy or queue policy
- `launch_surface="import"` preserves external provenance but does not convert imported evidence into runtime-owned scientific truth

## Change requirements

- Runtime entrypoints remain available and importable through this package.
- Runtime package documentation reflects ownership and dependency law.
- Runtime does not silently absorb lower-layer domain ownership.
- Runtime charter entries stay backed by live modules and a current source audit.
- Runtime docs must name the current owner modules and current route modules instead of removed topology labels.

Any contract change should update runtime surface tests and the boundary
validation suite that pins compat forwarding, canonical roots, and migration
ownership.

## Consumer upgrade expectations

- downstream users should be able to adopt routine releases without rewriting
  canonical CLI, API, or orchestration imports
- intentional entrypoint or provider-surface changes should be visible through
  explicit runtime tests and migration validation updates
- consumers should expect compat forwarding to keep mirroring canonical runtime
  ownership rather than diverging into a parallel implementation

## Change routing signals

- operator entrypoints, provider binding, replay-safe execution, and canonical
  runtime ownership belong here first
- lower-layer schema, lifecycle, evidence, ranking, and lab semantics should be
  routed back to their owning packages instead of being absorbed into runtime
- if compat needs wider legacy forwarding, the durable canonical surface change
  should land here before the compat package exposes it

## Validation checkpoints

- runtime surface tests should pin canonical CLI, API, orchestration, and
  provider entrypoints for the changed contract surface
- package-charter and boundary tests should stay green whenever module topology
  or canonical ownership changes
- boundary and migration validation should stay green whenever runtime widens a
  canonical surface that compat will mirror
- replay and adapter tests should preserve lower-layer runtime-agnostic
  contracts before operator-facing wrappers ship the new behavior

## Review questions

- does the contract change alter canonical operator entrypoints, provider
  binding, replay safety, or orchestration behavior
- would compat or lower packages otherwise start carrying shadow runtime-local
  transport or execution contracts
- can the contract still be justified without masking a missing lower-package
  contract

## Explicit non-contracts

- No compat deprecation policy is finalized in this document.
- No migration of domain semantics is implemented in this document.
- No long-term versioning policy override is introduced in this document.
