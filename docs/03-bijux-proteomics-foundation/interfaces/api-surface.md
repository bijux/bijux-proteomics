---
title: Python API Surface
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Python API surface

`bijux-proteomics-foundation` is a typed Python contract library. It publishes
no CLI, daemon, or HTTP routes. Its public surface is the package-root facade
plus documented modules for contracts that require more specialized control.

## Package-root facade

```python
from bijux_proteomics_foundation import (
    AssayId,
    BatchId,
    CandidateId,
    ClaimId,
    DocumentSchema,
    EvidenceId,
    GateId,
    JsonModel,
    ProgramId,
    TargetId,
    fingerprint_model,
    hash_model,
    hash_payload,
    hash_text,
    to_canonical_json,
)
```

| Group | Export | Meaning |
| --- | --- | --- |
| identity | `ProgramId`, `TargetId`, `CandidateId` | stable planning and candidate references |
| evidence | `ClaimId`, `EvidenceId` | claim-to-evidence linkage |
| operations | `AssayId`, `BatchId`, `GateId` | laboratory and release-control references |
| document metadata | `DocumentSchema` | versioned lifecycle and lineage envelope |
| model base | `JsonModel` | validated JSON, JSONL, TSV, file, and fingerprint helpers |
| canonical form | `to_canonical_json` | deterministic compact JSON representation |
| identity digest | `fingerprint_model`, `hash_model`, `hash_payload`, `hash_text` | SHA-256 content identity under the stable policy |

Root names are loaded lazily, so importing foundation does not eagerly import
every implementation module. An unknown root attribute raises
`AttributeError`; callers must not interpret a missing export as permission to
reach into private modules.

## Document lifecycle example

```python
from bijux_proteomics_foundation import DocumentSchema, to_canonical_json

metadata = DocumentSchema(
    created_by="quantification-workflow",
    document_id="evid-liver-cohort",
    document_kind="evidence_bundle",
    package_name="bijux-proteomics-core",
    status="reviewed",
    derived_from=["run-liver-dda"],
)

payload = {"protein_count": 412, "missingness_fraction": 0.08}
record = metadata.with_content_hash(payload).touch("release-reviewer")
serialized = to_canonical_json(record)

assert record.revision == 2
assert record.content_hash is not None
assert '"status":"reviewed"' in serialized
```

`DocumentSchema` forbids unknown fields, normalizes schema versions, uses UTC
timestamps, and returns copies from `touch()` and `with_content_hash()`. The
content hash covers the supplied payload, not the metadata object itself.

## Documented submodule contracts

| Module family | Use it for |
| --- | --- |
| `identity.identifiers` | the complete identifier vocabulary, prefix classification, construction, and validation |
| `serialization.*` | stable values, JSON normalization, fingerprints, and document schemas |
| `compatibility.*` | schema-version assessment, document migration, and import-movement records |
| `outcomes.*` | structured results, refusals, failures, exceptions, and optional-dependency behavior |
| `support.*` | provenance and shared state primitives |
| `testing.*` | repository test-policy helpers; these support maintainers, not product runtime consumers |

## Failure behavior

- Pydantic validation errors report malformed document fields and forbidden
  extras.
- Identifier helpers raise `ValueError` for empty suffixes or mismatched
  prefixes.
- Hashing and canonicalization propagate serialization errors for unsupported
  values.
- File helpers propagate filesystem errors; foundation does not retry writes or
  choose an artifact directory for the caller.
- Migration functions can reject unsupported version movement rather than
  manufacturing compatibility.

## Compatibility promise

Package-root removal or behavioral reinterpretation is a compatibility change.
Moving a documented submodule requires an import-migration record. Changing
canonicalization or hash policy can invalidate comparisons with persisted
artifacts and therefore requires explicit compatibility analysis. New internal
modules do not become public merely because Python can import them.
