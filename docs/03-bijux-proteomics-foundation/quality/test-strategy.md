---
title: Test Strategy
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Test strategy

Foundation testing follows shared meaning from construction through bytes,
version transitions, fingerprints, public imports, and real consumers. No
single layer proves the whole contract.

## Evidence layers

| Layer | Contract under test | Representative suite |
| --- | --- | --- |
| identity | valid, invalid, normalized, equal, unequal, and round-trip identifiers | `tests/identity/` |
| outcomes | success, failure, refusal, exception, and optional-dependency distinctions | `tests/outcomes/` |
| canonical values | supported scientific values, JSON normalization, ordering, and rejection | serialization primitive tests |
| document round trip | schema fields, version, validation, canonical bytes, and reconstruction | `test_document_roundtrip_surface.py` |
| compatibility | registered source/target versions, import migrations, aliases, and unsupported paths | `tests/compatibility/` |
| fingerprints and provenance | stable hashes, semantic change, source lineage, and transformation record | serialization and support tests |
| public boundary | exports, import direction, charter, type boundaries, and dependency discipline | `tests/package/` |
| consumer contract | downstream package reads and preserves the changed meaning | affected package boundary tests |

## Proof flow

```mermaid
flowchart LR
    C["constructor and invariant"] --> S["serialization"]
    S --> M["version and migration"]
    M --> H["fingerprint and provenance"]
    H --> A["public API"]
    A --> D["downstream consumer"]
```

Run the focused family first, then the package suite:

```bash
uv run --project packages/bijux-proteomics-foundation \
  pytest -q packages/bijux-proteomics-foundation/tests
```

When a public or persisted contract changes, run affected consumer tests in
Core, Knowledge, Intelligence, Lab, Runtime, and compatibility distributions
as applicable. A Foundation-only pass establishes local coherence, not
cross-package safety.

## Adversarial fixtures

Include unknown versions, missing and extra fields, invalid identifiers,
unsupported values, non-canonical ordering, lossy migration candidates,
changed provenance, and semantically distinct inputs with similar display
forms. Rejecting invalid state is part of the public contract.

Performance evidence for hashing and serialization protects resource behavior;
it does not replace value, migration, or consumer correctness tests.
