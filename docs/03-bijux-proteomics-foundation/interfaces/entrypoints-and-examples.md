---
title: Entrypoints and Examples
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Entrypoints And Examples

Use the package root for ubiquitous identifiers, document metadata, canonical
JSON, and stable hashes. Use documented submodules for identifier construction,
schema migration, structured outcomes, and other specialized contracts.

## Build And Validate An Identifier

```python
from bijux_proteomics_foundation.identity.identifiers import (
    IdentifierKind,
    build_identifier,
    ensure_identifier_kind,
)

assay_id = build_identifier(IdentifierKind.ASSAY, "MAPK1 confirmation")
ensure_identifier_kind(assay_id, IdentifierKind.ASSAY)
assert assay_id == "assay-mapk1-confirmation"
```

Construction normalizes the suffix and applies the stable kind prefix. It does
not resolve aliases or prove that the assay exists.

## Create A Durable Document Envelope

```python
from datetime import UTC, datetime

from bijux_proteomics_foundation import (
    DocumentSchema,
    hash_payload,
    to_canonical_json,
)

payload = {"assay_id": "assay-mapk1-confirmation", "replicates": 3}
recorded_at = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)

schema = DocumentSchema(
    created_by="lab-review",
    document_id="document-assay-mapk1-confirmation",
    document_kind="assay_plan",
    package_name="bijux-proteomics-lab",
    package_version="0.3.8",
    created_at=recorded_at,
    updated_at=recorded_at,
    status="reviewed",
).with_content_hash(payload)

document = {"document_schema": schema.to_dict(), "payload": payload}
canonical = to_canonical_json(document)

assert schema.content_hash == hash_payload(payload)
assert canonical == to_canonical_json(document)
```

Use an explicit timestamp when reproducing exact fixture bytes. Default
timestamps are correct for new records but intentionally make separately
created envelopes differ.

## Declare A Schema Migration

```python
from copy import deepcopy

from bijux_proteomics_foundation.compatibility.schema_migrations import (
    MigrationRegistry,
    SchemaMigration,
)


def add_review_status(document: dict[str, object]) -> dict[str, object]:
    migrated = deepcopy(document)
    metadata = migrated["document_schema"]
    assert isinstance(metadata, dict)
    metadata["schema_version"] = "1.1.0"
    payload_data = migrated["payload"]
    assert isinstance(payload_data, dict)
    payload_data.setdefault("review_status", "pending")
    return migrated


registry = MigrationRegistry()
registry.register(
    SchemaMigration(
        from_version="1.0.0",
        to_version="1.1.0",
        description="make review status explicit",
        migrate=add_review_status,
    )
)

migrated = registry.migrate_to(document, "1.1.0")
```

The registry proves that a declared path can run and reaches the expected
version. Validate `migrated` against the target payload model before accepting
it. Missing paths, cycles, deprecated targets, and unexpected output versions
are failures—not invitations to guess.

## Choose The Right Surface

| Need | Import route |
| --- | --- |
| common typed IDs, `DocumentSchema`, canonical JSON, stable hashes | `bijux_proteomics_foundation` |
| identifier construction and classification | `bijux_proteomics_foundation.identity.identifiers` |
| migrations and version compatibility | `bijux_proteomics_foundation.compatibility` |
| refusals, exceptions, and typed outcomes | `bijux_proteomics_foundation.outcomes` |
| provenance and specialized serialization helpers | documented owner module |

Foundation has no CLI or service entrypoint. Callers needing execution,
scientific analysis, evidence custody, decision policy, or laboratory workflow
must use the package that owns that behavior.
