---
title: Common Workflows
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Contract kernel workflows

Foundation workflows are deliberately small. They establish a typed value,
turn it into stable bytes, identify it, and recover or migrate it without
requiring a scientific or execution package.

## Create a governed document

Use `DocumentSchema` for persisted records that need package identity, document
kind, schema version, and creation provenance. Keep domain payloads separate
from the envelope so a consumer can validate governance fields before loading
package-specific content.

Serialize with `to_canonical_json()` when bytes or hashes cross a process,
artifact, cache, or review boundary. Canonical serialization normalizes the
supported scientific values and produces deterministic key ordering; ordinary
`json.dumps()` settings are not a substitute for that contract.

```python
from bijux_proteomics_foundation import DocumentSchema, hash_payload
from bijux_proteomics_foundation import to_canonical_json

schema = DocumentSchema(
    created_by="example-pipeline",
    document_kind="evidence_summary",
    package_name="bijux-proteomics-knowledge",
)
payload = {"schema": schema.model_dump(mode="json"), "claim_ids": ["claim:1"]}

canonical = to_canonical_json(payload)
digest = hash_payload(payload)
assert canonical.startswith("{")
assert len(digest) == 64
```

Store the digest with the envelope or manifest that names the hashing contract.
A bare digest without the canonicalization rules cannot prove equivalence.

## Load and migrate persisted input

Read the envelope before the payload. Compare the recorded schema version with
the consumer's supported versions and choose one explicit outcome:

1. accept the document unchanged;
2. migrate through a registered, ordered schema route;
3. reject it with a machine-readable compatibility reason.

Migration produces a new governed document. Preserve the source version and
digest so reviewers can reconstruct the transformation. Never mutate an old
artifact in place or infer a missing version from its newest-looking fields.

## Return structured outcomes

Use the Foundation result and exception contracts when callers need to
distinguish a valid result from a validation, compatibility, or execution
failure. Retain causal details and identifiers in the typed outcome; logs are
diagnostic views, not the result contract.

## Verify cross-package use

For any changed shared contract, select at least one producing package and one
consuming package. Prove the sequence `model -> canonical bytes -> persisted
document -> load/migrate -> model`, then compare both the typed value and its
digest. This catches changes that isolated model validation cannot see.

The workflow is complete when validation is explicit, serialization is
deterministic, schema compatibility has a declared result, and consumers do
not need package-local coercion to interpret the shared value.
