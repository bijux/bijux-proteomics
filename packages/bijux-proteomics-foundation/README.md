# bijux-proteomics-foundation

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-foundation/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-foundation/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

`bijux-proteomics-foundation` is the shared contract kernel for the package
family, including canonical JSON behavior, deterministic hashing, document
fingerprints, and compatibility contracts for persisted scientific records.

Within the suite, foundation owns shared contracts, identifiers, and
deterministic serialization.

Use this package when you need versioned document governance, migration-safe
serialization, and cross-package consistency for reproducible proteomics data.

## At a glance

- Use foundation when the problem is shared document identity, canonical JSON,
  compatibility checks, or durable hashing across package boundaries.
- Start with the stable root imports for shared contracts, then open the
  [foundation handbook](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
  when you need the full owner surface.
- Route scientific meaning to core, execution to runtime, recommendation
  posture to intelligence, scientific memory to knowledge, and assay follow-up
  to lab.

## Why teams pick this kernel

- one canonical document-contract baseline across every proteomics package
- stable fingerprints for cache keys, lineage, and provenance checks
- compatibility helpers for migration-safe long-lived scientific records
- small shared primitives that keep downstream packages from rebuilding the
  same durable contract logic

## Typical use cases

- define document metadata with explicit version and compatibility policy
- serialize domain models into canonical JSON for reproducible comparisons
- validate migration paths before accepting persisted record upgrades
- centralize shared contract behavior so other packages stay focused on domain logic

## 0.3.8 Release Highlights

- The shared kernel now covers canonical document metadata, JSON rendering,
  stable hashing, identifier kinds, refusal and result envelopes, and schema
  compatibility checks in one bounded package.
- Foundation also ships the shared optional-dependency guards, alias helpers,
  generated-file markers, and reusable test-policy primitives that the release
  gates now depend on.
- The public root stays intentionally small while durable owner families make
  long-term boundaries explicit for contributors and downstream packages.

## Installation

```bash
pip install bijux-proteomics-foundation
```

Test install:

```bash
pip install -e '.[test]'
```

## Quick start

```python
from bijux_proteomics_foundation import DocumentSchema, hash_payload, to_canonical_json
```

## Public APIs

The stable root API is intentionally small:

- `DocumentSchema` for durable metadata on persisted artifacts
- `to_canonical_json(...)` for deterministic serialization
- `hash_payload(...)`, `hash_text(...)`, and `hash_model(...)` for reproducible fingerprints
- `JsonModel` plus typed identifiers such as `ProgramId`, `TargetId`, and `ClaimId`

Minimal executable example:

```python
from bijux_proteomics_foundation import DocumentSchema, hash_payload, to_canonical_json

schema = DocumentSchema(
    created_by="bijux-proteomics-foundation",
    document_kind="readme_example",
    package_name="bijux-proteomics-foundation",
)
payload = {
    "document_kind": schema.document_kind,
    "schema_version": schema.schema_version,
}
rendered = to_canonical_json(payload)
fingerprint = hash_payload(payload)

assert '"readme_example"' in rendered
assert len(fingerprint) == 64
```

## Package identity

- Distribution name: `bijux-proteomics-foundation`
- Import root: `bijux_proteomics_foundation`
- Stable entrypoints:
  `bijux_proteomics_foundation`, `compatibility`, `identity`, `outcomes`,
  `serialization`, and `support`

## Package boundaries

This package owns shared document metadata, canonical serialization, and
migration compatibility helpers as a shared kernel rather than a user-facing
workflow package.

It does not own product decision logic, lab logic, or runtime orchestration.
The exact allowed primitive surface is audited in `support/charter.py`.

## What this package must not do

- it must not define workflow orchestration, provider binding, or operator entrypoints
- it must not own scientific evidence semantics, recommendation policy, or lab planning rules
- it must not become a generic dumping ground for single-package helpers that do not belong in the shared kernel

## Contract checkpoints

- equivalent models must serialize to identical canonical JSON and fingerprints
- compatibility evaluation must report explicit status and reason text
- migrations must preserve semantic meaning while advancing declared versions
- downstream packages may depend on these primitives, but should not move domain rules into this layer

## Contract examples

These examples stay at the shared-kernel layer. Workflow-owned, CLI-owned, and
runtime-owned examples belong in the package that owns that behavior.

Document metadata:

```python
from bijux_proteomics_foundation import DocumentSchema

schema = DocumentSchema(
    created_by="bijux-proteomics-foundation",
    document_kind="contract_bundle",
    package_name="bijux-proteomics-foundation",
    package_version="0.3.8",
)
```

Identifiers:

```python
from bijux_proteomics_foundation.identity.identifiers import (
    IdentifierKind,
    build_identifier,
)

run_id = build_identifier(IdentifierKind.RUN, "Orbitrap Batch 7")
```

Canonical serialization and hashing:

```python
from bijux_proteomics_foundation import hash_payload, to_canonical_json

payload = {"a": 1, "b": 2}
fingerprint = hash_payload(payload)
rendered = to_canonical_json(payload)
```

Refusals:

```python
from bijux_proteomics_foundation.outcomes.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.support.states import SupportState

refusal = OperationRefusal(
    operation="artifact_validation",
    kind=RefusalKind.UNSUPPORTED,
    code="unsupported_construct",
    reason="the payload cannot be normalized without changing shared meaning",
    support_state=SupportState.REFUSED,
)
```

Error envelopes:

```python
from bijux_proteomics_foundation.outcomes.failures import (
    ErrorCategory,
    ErrorEnvelope,
)

envelope = ErrorEnvelope(
    category=ErrorCategory.RUNTIME,
    code="contract_rejection",
    message="canonical document validation rejected the payload",
)
```

Operation results:

```python
from bijux_proteomics_foundation.outcomes.results import OperationResult

result = OperationResult.success(
    operation="contract_validation",
    summary="shared contract validation completed successfully",
    output_fingerprint="a" * 64,
)
```

## Choose this package when

- you need reusable schema, serialization, identifier, or migration primitives
- the same document contract must stay consistent across multiple package layers
- the change is low-volatility shared infrastructure rather than package-specific
  domain behavior

## Route elsewhere when

- the change defines lifecycle, ranking, evidence, lab, or runtime semantics
- the helper would only serve one higher-layer package instead of the shared
  family
- the work mainly reshapes transport or orchestration payloads instead of shared
  document primitives

## Verification route

- check `tests` for schema, serialization, and migration proof before treating a
  foundation change as safe
- review `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
  when ownership or stability claims are part of the change
- review `support/charter.py` when the question is whether a new primitive belongs in
  foundation at all
- use `README.md`, `CHANGELOG.md`, and package `docs/*.md` when the change
  affects package publication, metadata, or release-readiness expectations

## Review questions

- does the change preserve reusable schema, serialization, identifier, or
  migration behavior rather than higher-layer policy or execution logic
- would two or more downstream packages otherwise duplicate or drift on the
  same document primitive if this stayed outside foundation
- can the change be justified without claiming lifecycle, evidence, ranking,
  lab, or runtime orchestration ownership

## Escalation route

- route the change upward when the primitive only serves one domain package
  instead of the shared family
- stop and review `docs/BOUNDARIES.md` and `docs/ARCHITECTURE.md` when the
  proposal starts carrying lifecycle, evidence, ranking, lab, or runtime terms
- escalate to the owning higher-layer package before release when downstream
  consumers would need package-specific exceptions to adopt the change

## Consumer impact signals

- expect broad downstream review when schema, serialization, identifier, or
  migration primitives change because every package may consume them
- treat changes that alter canonical JSON, fingerprints, or compatibility
  status as high-impact even when APIs stay stable
- expect a lower release burden when the change only tightens internal
  implementation without changing shared document behavior

## Explicit non-goals

- this package does not define lifecycle, evidence, ranking, lab, or runtime
  semantics
- this package does not coordinate workflow-local adapters or operator-facing
  orchestration
- this package does not carry compatibility-only shims that belong in a higher
  canonical layer or in the compat package

## Source guide

- [`src/bijux_proteomics_foundation/serialization/document_schema.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/serialization/document_schema.py) for document metadata and audit lineage
- [`src/bijux_proteomics_foundation/serialization/scientific_values.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/serialization/scientific_values.py) for nullability, duration, timestamp, and coordinate wrappers
- [`src/bijux_proteomics_foundation/compatibility/schema_assessments.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/compatibility/schema_assessments.py) for compatibility and schema-evolution assessments
- [`src/bijux_proteomics_foundation/serialization/canonical_json.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/serialization/canonical_json.py) for canonical serialization
- [`src/bijux_proteomics_foundation/serialization/stable_hashes.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/serialization/stable_hashes.py) for deterministic hashing policies
- [`src/bijux_proteomics_foundation/serialization/json_contracts.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/serialization/json_contracts.py) for reusable JSON-backed contract helpers
- [`src/bijux_proteomics_foundation/identity/identifiers.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/identity/identifiers.py) for shared identifier contracts
- [`src/bijux_proteomics_foundation/support/provenance.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/support/provenance.py) for provenance pointers and adjacent support-state contracts
- [`src/bijux_proteomics_foundation/outcomes/failures.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/outcomes/failures.py) for structured machine-readable failure contracts
- [`src/bijux_proteomics_foundation/outcomes/results.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/outcomes/results.py) for shared refusal and operation-result contracts
- [`src/bijux_proteomics_foundation/compatibility/schema_migrations.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/compatibility/schema_migrations.py) for migration behavior
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-foundation/tests) for executable behavior expectations

## Documentation

- [Product overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-overview/)
- [Workflow families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Package guide](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
- [Ownership boundary](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/ownership-boundary/)
- [Architecture overview](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/)
- [Interface contracts](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/)
- [Release and versioning](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/release-and-versioning/)
