---
title: Python Entry Points
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Python entry points

`bijux-proteomics-foundation` is a typed library and deliberately installs no
command-line executable. It defines the identity, serialization, hashing,
schema-evolution, and outcome contracts used by commands in higher-level
packages. A standalone foundation CLI would have to invent application policy:
which document to read, which migration registry to load, and where to write
the result.

Use the curated package root for the smallest stable surface:

```python
from bijux_proteomics_foundation import (
    DocumentSchema,
    ProgramId,
    hash_payload,
    to_canonical_json,
)

schema = DocumentSchema(
    created_by="review-service",
    document_id="program-demo",
    document_kind="program_spec",
)

payload = {"document_schema": schema.to_dict(), "program_id": "prog-demo"}
canonical = to_canonical_json(payload)
digest = hash_payload(payload)
```

`ProgramId` and the other identifier aliases are Pydantic-compatible annotated
strings. For prefix construction and classification, import
`IdentifierKind`, `build_identifier()`, and `ensure_identifier_kind()` from
`bijux_proteomics_foundation.identity`.

## Where command-line behavior belongs

| Need | Owning surface |
| --- | --- |
| Validate a domain document | The package that defines that document model |
| Execute or reproduce a run | `bijux-proteomics-runtime` |
| Inspect scientific data | `bijux-proteomics-core` |
| Check repository contracts | `bijux-proteomics-dev` maintainer commands |
| Convert a foundation model to JSON, JSONL, or TSV | `JsonModel` methods in application code |

Foundation raises typed validation, migration, serialization, and optional
dependency errors; a consuming CLI decides how those failures map to exit
codes and terminal or JSON output. This separation keeps the same contract
usable from a notebook, service, batch worker, or command without transport
behavior changing its meaning.
