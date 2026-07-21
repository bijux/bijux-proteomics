---
title: Installation and Setup
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Installation and Setup

`bijux-proteomics-foundation` is the lightweight contract kernel for the package family. Install it directly when an application needs canonical JSON, stable fingerprints, shared identifiers, schema compatibility, or typed outcome envelopes without higher-level scientific or execution packages.

## Requirements

- Python 3.11 or newer
- an isolated Python environment
- Pydantic 2, installed automatically as the sole runtime dependency

## Install from PyPI

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install bijux-proteomics-foundation
```

Confirm the import and canonicalization contract:

```python
from bijux_proteomics_foundation import hash_payload, to_canonical_json

left = {"run": "run-7", "score": 0.91}
right = {"score": 0.91, "run": "run-7"}

assert to_canonical_json(left) == to_canonical_json(right)
assert hash_payload(left) == hash_payload(right)
```

This verifies deterministic mapping order. It does not establish scientific equivalence, authenticity, or data quality; those properties need provenance and domain validation from their owning packages.

## Install a source checkout

From the repository root:

```bash
python -m pip install -e "packages/bijux-proteomics-foundation[test]"
python -m pytest packages/bijux-proteomics-foundation/tests
```

The `test` extra adds property-based tests, benchmark support, and biological test dependencies. It is not required by downstream applications.

## Verify a persisted-document path

For code that reads durable artifacts, test more than serialization:

1. Construct or load the document's `DocumentSchema`.
2. Evaluate compatibility through `compatibility.schema_assessments`.
3. Resolve an explicit migration path through `MigrationRegistry` when required.
4. Re-serialize and fingerprint the migrated result.
5. Compare the scientific fields and provenance expected by the consuming package.

Never rewrite stored data merely to make validation pass. A missing migration edge is an explicit `MigrationPathError`; an unexpected version after migration is a `MigrationExecutionError`.

## Dependency placement

Depend on Foundation from a package that owns cross-package contracts. Do not require users to install it separately when a higher-level Bijux package already declares it. Conversely, do not install Core or Runtime just to use hashing or identifiers—the kernel is intentionally usable without them.
