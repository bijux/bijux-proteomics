# bijux-proteomics-runtime

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-runtime/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-runtime/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

`bijux-proteomics-runtime` is the execution owner for provider binding,
deterministic replay, and operator-facing orchestration surfaces in
`bijux-proteomics`.

Within the suite, runtime owns execution, provider binding, deterministic
replay, and operator entrypoints.

Use this package when you need supported CLI, HTTP API, provider wiring,
runtime state handling, and replay-safe orchestration for the bounded
flagship workflow chain.

Runtime owns execution control. It does not own the scientific workflow
blueprint, evidence truth, ranking semantics, or lab progression logic that the
wider proteomics engine still needs.

## At a glance

- Use runtime when the concern is executable workflow control, provider
  binding, deterministic replay, or operator-facing handoff.
- Start with `bijux-proteomics-runtime --help` for the live CLI surface, then
  open the
  [runtime handbook](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
  when you need the end-to-end run path.
- Route scientific truth to core, cited evidence memory to knowledge,
  recommendation posture to intelligence, and assay follow-up authority to
  lab.

## Why teams pick this package

- one canonical runtime surface for CLI, API, orchestration, and providers
- deterministic replay and artifact shaping for repeatable execution outcomes
- typed run context, artifact ledger, replay contract, and local/container/scheduler/import run bundle outputs
- runtime-owned CLI and API operations that avoid private helper glue
- reviewable run and import paths that publish canonical downstream-facing manifests
- partial rerun planning, cache claims, cleanup plans, and failure-recovery audits for operational safety
- preflight and failure reports that fail early on missing execution requirements
- import traces, human-review resume checkpoints, and artifact-integrity reports for safe reuse
- runtime-owned control surfaces that consume lower-layer contracts without re-exporting their domain semantics
- explicit migration target for `agentic-proteins` compatibility forwarding

## Typical use cases

- run the canonical proteomics workflow through CLI or HTTP entrypoints
- bind local or API-backed structure providers behind one orchestration layer
- enforce replay-safe runtime execution without moving domain semantics upward
- ingest third-party engine outputs while preserving external provenance honestly
- publish one useful run path from clean install to reviewable output
- publish one useful import-only path from third-party result to reviewable output
- integrate canonical runtime surfaces while legacy imports remain compat-only

## 0.3.8 Release Highlights

- Runtime now publishes advanced DIA-NN dry-run, resume, comparison, archive,
  and architecture-demo workflows as public owner surfaces.
- Workflow DAG typing, semantic cache fingerprints, partial rerun plans,
  workflow failure artifacts, and reviewable handoff archives now stay
  machine-readable instead of living in ad hoc runtime glue.
- Black-box rerun and reviewable sequence/import paths are now explicit parts
  of the runtime trust story rather than maintainer-only knowledge.

## Installation

```bash
pip install bijux-proteomics-runtime
```

## Quick start

Use the runtime CLI for end-to-end workflow execution, replay, and reviewable
run outputs:

```bash
bijux-proteomics-runtime --help
```

Use exact owner modules for Python integrations:

```python
from bijux_proteomics_runtime.api.app import AppConfig, create_app
from bijux_proteomics_runtime.runs.manager import RunManager
from bijux_proteomics_runtime.workflows.paths import (
    run_reviewable_import_path,
    run_reviewable_sequence_path,
)
```

The package root remains a stable external entrypoint surface, but runtime
maintainers and in-repo consumers should import the exact owner modules above
instead of widening `bijux_proteomics_runtime` into a convenience bucket.

## Public APIs

The stable root API stays intentionally small:

- `AppConfig` for runtime app configuration
- `create_app(...)` for the canonical FastAPI assembly path
- `RunManager` for execution coordination
- `api.cli:cli` for the supported operator command surface

Minimal executable example:

```python
from pathlib import Path

from bijux_proteomics_runtime import AppConfig, create_app

base_dir = Path("artifacts/readme-runtime-app")
app = create_app(AppConfig(base_dir=base_dir, docs_enabled=False))

assert app.state.base_dir == base_dir
assert app.docs_url is None
assert any(route.path == "/health" for route in app.routes)
```

## Package identity

- Distribution name: `bijux-proteomics-runtime`
- Import root: `bijux_proteomics_runtime`
- Flagship workflow CLI command: `bijux-proteomics-runtime`
- Stable entrypoints: `AppConfig`, `RunManager`, `create_app`, and `api.cli:cli`
- Execution charter: `src/bijux_proteomics_runtime/governance/charter.py`
- First-level owner families: `api/`, `execution/`, `governance/`, `providers/`, `runs/`, `state/`, `support/`, and `workflows/`
- Compatibility forwarding lives in `agentic-proteins`; the canonical runtime package keeps only owner paths

## Package boundaries

This package owns runtime execution behavior and orchestration interfaces.

Domain meaning, evidence semantics, scoring policy, and lab planning semantics
remain in their dedicated lower-layer packages.

## What this package must not do

- it must not redefine scientific workflow truth, evidence truth, or recommendation policy
- it must not absorb knowledge curation or lab execution semantics into runtime transport
- it must not pretend container orchestration, scheduler policy, or external-engine provenance are runtime-owned science

## Execution charter

- `governance/charter.py` defines the exact runtime-owned capability boundary and classifies every source module against it
- runtime only owns canonical entrypoints, provider binding, workflow execution, replay and recovery, and reviewable run outputs
- modules that cannot be defended against that charter should move out of runtime or be deleted rather than hardening into generic infrastructure

## Supported execution surfaces

Launch surfaces:

- `launch_surface="local"` runs through `runs/manager.py` inside the current workspace and persists canonical review artifacts
- `launch_surface="container"` emits container launch bundles and digest capture through `runs/launch_bundles.py`; runtime does not build images or define container fleet policy
- `launch_surface="scheduler"` emits scheduler submission bundles and replay-safe metadata through `runs/launch_bundles.py`; runtime does not own queue policy, job priority rules, or cluster provisioning
- `launch_surface="import"` normalizes third-party outputs through `runs/import_lineage.py`; runtime does not claim new scientific derivation for imported evidence

Execution modes:

- `execution_mode="auto"` lets provider capability checks choose an allowed mode; runtime may degrade to CPU when provider support or configured budgets require it
- `execution_mode="cpu"` forces CPU-compatible execution; runtime does not emulate GPU-only providers when a CPU path is unavailable
- `execution_mode="gpu"` requires GPU-capable providers and an execution environment that can honor that request; runtime does not provision GPUs or schedule cluster policy

Non-goals for these surfaces:

- runtime does not define workflow truth, evidence truth, scoring truth, or lab truth
- runtime does not promise every provider on every launch surface
- runtime does not replace container orchestration, scheduler administration, or external-engine provenance

## Canonical owner imports

- `bijux_proteomics_runtime.api.cli` for CLI contracts and operator-safe command output
- `bijux_proteomics_runtime.api.app` for `AppConfig`, FastAPI construction, and request-scoped runtime wiring
- `bijux_proteomics_runtime.api.routes.runtime_execution` for runtime execution HTTP routes
- `bijux_proteomics_runtime.runs.manager` for canonical execution coordination
- `bijux_proteomics_runtime.runs.preflight` for readiness and refusal reports
- `bijux_proteomics_runtime.runs.replay_decisions` and `runs.execution_decisions` for operator-visible reuse and degraded-mode reasoning
- `bijux_proteomics_runtime.runs.import_lineage` for import traces and derived-artifact separation
- `bijux_proteomics_runtime.workflows.paths` for reviewable runtime path manifests
- `bijux_proteomics_runtime.providers.selection` and `providers.capabilities` for provider binding and capability gates

## Operational review paths

- `run_reviewable_sequence_path` publishes a runtime-owned manifest from canonical execution to reviewable output
- `run_reviewable_import_path` publishes a runtime-owned manifest from third-party evidence import to reviewable output
- `build_runtime_smoke_workflows` declares the supported smoke paths for sequence-to-digest, DDA import, DIA import, quant review, PTM review, analytical review, and lab handoff
- `build_runtime_partial_rerun_plan` exposes dependency-graph rerun boundaries instead of leaving replay reuse implicit
- `build_runtime_preflight_report`, `verify_runtime_artifact_integrity`, and `write_runtime_failure_report` keep readiness, reuse safety, and failure classification on explicit run-owned support surfaces

## Contract checkpoints

- runtime entrypoints must remain canonical while compat imports forward to them
- lower-layer meaning must stay below runtime owner families rather than being redefined here
- replay, artifact, and provider contracts must remain explicit and testable
- run context, artifact ledger, replay/import bundles, checkpoint artifacts, and preflight outputs must remain machine-readable and reviewable
- changes to canonical ownership should land in runtime before compat forwarding expands

## Foundation-backed runtime contract examples

Runtime-owned examples that depend on shared foundation primitives stay here so
the foundation package does not read like a workflow product.

Document metadata:

```python
from bijux_proteomics_foundation import DocumentSchema

schema = DocumentSchema(
    created_by="bijux-proteomics-runtime",
    document_kind="artifact_bundle",
    package_name="bijux-proteomics-runtime",
    package_version="0.3.8",
)
```

Runtime refusal:

```python
from bijux_proteomics_foundation.outcomes.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.support.states import SupportState

refusal = OperationRefusal(
    operation="mzidentml_ingestion",
    kind=RefusalKind.UNSUPPORTED,
    code="unsupported_construct",
    reason="the source export cannot be normalized honestly",
    support_state=SupportState.REFUSED,
)
```

Runtime error envelope:

```python
from bijux_proteomics_foundation.support.error_models import (
    ErrorCategory,
    ErrorEnvelope,
)

envelope = ErrorEnvelope(
    category=ErrorCategory.RUNTIME,
    code="engine_timeout",
    message="external engine did not complete before timeout",
)
```

Runtime operation result:

```python
from bijux_proteomics_foundation.outcomes.results import OperationResult

result = OperationResult.success(
    operation="hash_manifest",
    summary="hash computed successfully",
    output_fingerprint="a" * 64,
)
```

## Choose this package when

- you need canonical CLI, API, provider binding, or replay-safe orchestration
- the change affects how canonical execution runs rather than what lower layers mean
- operator-facing entrypoints or runtime control helpers need to evolve without pushing
  runtime ownership downward

## Route elsewhere when

- the change defines schema, lifecycle, evidence, ranking, or lab semantics
- the helper only exists to preserve historical imports instead of canonical
  runtime behavior
- the provider-specific rule would force lower packages to import runtime

## Verification route

- check `tests` for runtime surface, provider, replay, and migration proof
  before treating a runtime change as safe
- review `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
  when canonical ownership or adapter law is part of the change
- use `README.md`, `CHANGELOG.md`, and package `docs/*.md` when the change
  affects package publication, metadata, or release-readiness expectations

## Review questions

- does the change preserve canonical operator entrypoints, provider binding, or
  replay-safe orchestration rather than lower-layer domain semantics
- would compat or lower packages start carrying shadow execution transport or
  adapter law if this behavior stayed outside runtime
- can the change be justified as runtime-local work instead of a missing lower
  package contract or a compat-only bridge

## Escalation route

- route the change downward when the behavior actually defines schema,
  lifecycle, evidence, ranking, or lab semantics
- stop and review `docs/BOUNDARIES.md` and `docs/ARCHITECTURE.md` when the
  proposal starts looking like compatibility glue or provider-specific policy
  rather than canonical runtime orchestration
- escalate before release when adopting the change would force lower packages or
  compat surfaces to mirror new runtime-local exceptions

## Consumer impact signals

- expect cross-surface review when CLI, API, provider binding, replay behavior,
  or migration expectations change because operators consume them directly
- treat changes that alter canonical entrypoints, runtime control helpers, or compat
  expectations as high-impact even when import paths stay stable
- expect a narrower release burden when the change only improves internal
  orchestration without changing runtime-facing behavior

## Explicit non-goals

- this package does not redefine schema, lifecycle, evidence, ranking, or lab
  semantics owned by lower layers
- this package does not serve as a dumping ground for compat-only exceptions or
  migration shims
- this package does not decide scientific truth, only how canonical execution
  runs over lower-layer contracts
- this package does not substitute for an end-to-end scientific workflow model
  across core, intelligence, knowledge, and lab

## Source guide

- [`src/bijux_proteomics_runtime/runs`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/runs) for typed run contracts, canonical run operations, and execution ownership
- [`src/bijux_proteomics_runtime/workflows`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows) for workflow planning, reproducibility, reviewable path manifests, and execution assurance ledgers
- [`src/bijux_proteomics_runtime/governance/charter.py`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/governance/charter.py) for the machine-readable execution charter and module audit
- [`src/bijux_proteomics_runtime/api/cli.py`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api/cli.py) for CLI contracts
- [`src/bijux_proteomics_runtime/api`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api) for HTTP entrypoints
- [`src/bijux_proteomics_runtime/providers`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/providers) for provider cataloging, capability gates, selection, and execution environment contracts
- [`src/bijux_proteomics_runtime/support`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/support) for execution primitives, artifact format contracts, and workspace support
- [`artifacts/<run-id>`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime) for persisted runtime bundle, checkpoint, and integrity outputs at execution time
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/tests) for executable surface and migration expectations

## Documentation

- [Advanced DIA-NN Python API tutorial](docs/ADVANCED-DIANN-PYTHON-API.md)
- [Execution overview](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
- [Operator rerun journey](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operator-rerun-journey/)
- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Public surfaces dossier](docs/PUBLIC-SURFACES.md)
- [Route ownership dossier](docs/ROUTE-OWNERSHIP.md)
- [Provider ownership dossier](docs/PROVIDER-OWNERSHIP.md)
- [Artifact lineage dossier](docs/ARTIFACT-LINEAGE.md)
- [Benchmark rerun kits](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/benchmark-rerun-kits/)
- [Package guide](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
- [Runtime execution boundary](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-execution-boundary/)
- [Runtime environment contracts](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-environment-contracts/)
- [Runtime artifact stability](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-artifact-stability/)
- [Repository release and versioning](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/release-and-versioning/)
