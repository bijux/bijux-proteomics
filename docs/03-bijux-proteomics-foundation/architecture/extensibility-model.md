---
title: Extensibility Model
audience: developer
type: architecture
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Extensibility Model

Foundation should grow more slowly than the packages above it. Every public
addition expands the vocabulary, serialization surface, and compatibility
burden of the entire repository. Extend an existing contract family whenever
possible; introduce a new family only for proven, identical cross-package
meaning.

## Admission test

A new foundation contract must satisfy all of these conditions:

1. At least two independent product owners exchange the same durable meaning.
2. The meaning can be defined without execution, evidence-ranking, scientific,
   or laboratory policy.
3. Producers and consumers can validate the contract independently.
4. Canonical JSON, ordering, fingerprint behavior, and version evolution are
   specified.
5. Success, degradation, refusal, and failure behavior are explicit where the
   operation can be partial.
6. The public API ledger can state why any root export belongs in the kernel.

## Preferred extension paths

| Need | Extend | Required companion work |
| --- | --- | --- |
| New cross-package identity | `identity/identifiers.py` | validation, JSON round trip, and downstream join tests |
| New document metadata | `serialization/document_schema.py` | schema version decision, hash boundary, and migration assessment |
| New fingerprint purpose | `serialization/fingerprints.py` | named scope, canonicalization policy, and collision-independent semantics |
| New compatibility edge | `compatibility/schema_migrations.py` | one-direction migration, path validation, and current-model validation |
| New partial outcome | existing support, refusal, and result contracts | precise invariant; avoid adding another outcome vocabulary |
| New provenance locator | `support/provenance.py` | serialization, ordering, and dereference responsibility |

## Evolution rules

Never change the meaning of an existing field in place. Add a schema version
and an explicit migration when stored documents require transformation. A
migration must produce its declared target version and should be deterministic,
side-effect free, and independently testable. Deprecating a version blocks it
as a migration target; it does not excuse removal of the path needed to read
historical data.

Root exports are rarer than module-level contracts. Most consumers should
import from the owning family unless the symbol is a kernel primitive covered
by the root API budget. Compatibility aliases may preserve old paths, but they
must not become an alternate implementation.

## Extension smells

- one product package is the only real consumer;
- a generic field hides domain-specific units or states;
- a hash is described as proof of origin or scientific equality;
- optional dependencies are imported eagerly;
- a permissive parser replaces versioned migration;
- success is represented by absence of an error; or
- a root export is added because its owning path feels inconvenient.

An extension is complete when downstream packages can exchange it without
semantic translation, historical documents have a defined path, deterministic
round trips are verified, and the kernel remains independent of product policy.
