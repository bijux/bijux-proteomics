---
title: Python API Surface
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Python API surface

Foundation is a Python contract library. It does not run an HTTP service or
publish a CLI. Its supported entry points are the curated package-root exports
and explicit submodule contracts.

## Root imports

```python
from bijux_proteomics_foundation import (
    DocumentSchema,
    ProgramId,
    JsonModel,
    hash_payload,
    to_canonical_json,
)
```

| Capability | Root exports |
| --- | --- |
| identity | `AssayId`, `BatchId`, `CandidateId`, `ClaimId`, `EvidenceId`, `GateId`, `ProgramId`, `TargetId` |
| document contract | `DocumentSchema` |
| JSON model contract | `JsonModel`, `fingerprint_model` |
| canonical serialization | `to_canonical_json` |
| stable hashing | `hash_model`, `hash_payload`, `hash_text` |

These names are lazily loaded and governed by the root API ledger. Callers
should prefer them when the primitive is listed above; internal helper modules
are not substitutes for a missing public export.

## Submodule contracts

- `identity.identifiers` defines the complete typed identifier set.
- `serialization.document_schema` defines schema envelopes.
- `serialization.json_contracts` defines model serialization and
  fingerprinting.
- `serialization.scientific_values` and `stable_values` define accepted
  normalization behavior.
- `compatibility.schema_versions`, `schema_assessments`, and
  `schema_migrations` govern document evolution.
- `compatibility.import_migrations` describes Python import movement.
- `outcomes.results`, `failures`, `refusals`, and `optional_dependencies`
  preserve non-success semantics.
- `support.provenance` and `support.states` provide shared provenance and state
  primitives.

## Stability rules

Root exports are the narrowest compatibility surface. A submodule is public
only when it is documented and included in the package's API governance. A
consumer must not import underscore-prefixed modules or rely on implementation
layout. Schema compatibility and Python import compatibility are reviewed
separately.

Network APIs belong to consuming packages, principally
`bijux-proteomics-runtime`. They may use foundation schemas but own their HTTP
routes, request validation, authentication boundary, and response behavior.
