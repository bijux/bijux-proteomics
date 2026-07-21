---
title: Security and Safety
audience: developer
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Security and Safety

Foundation protects the semantic boundary between packages. Its strict models,
explicit versioning, deterministic serialization, typed refusals, and stable
provenance records reduce ambiguity; they do not replace application security,
authorization, or scientific review.

## Validate at ingress

Parse untrusted documents into the narrowest applicable model before using
their values. Core contracts reject extra fields so misspellings and unexpected
producer data cannot silently acquire meaning. Keep this strictness when
extending a schema. New optional fields require defined semantics and version
compatibility, not only a default value.

Migration functions execute code supplied by the application. Register only
reviewed migrations, require an unbroken source-to-target path, migrate a copy,
and validate the result. A migration is a semantic transformation, so it must
not fetch remote content, read credentials, or infer missing scientific values
from ambient state.

## Understand integrity claims

Canonical SHA-256 fingerprints are useful for cache keys, replay comparisons,
and change detection. They are not signatures. A matching digest does not prove
the producer's identity, authorization, source quality, or scientific validity.
Applications that require authenticity must add an authenticated envelope and
manage keys outside foundation contracts.

Likewise, a `ProvenancePointer` records a locator and optional fingerprint; it
does not open, fetch, or trust that resource. Treat URIs and labels as data.
Validate schemes and access policy in the package that dereferences them, and
never interpolate provenance text into shell commands or queries.

## Keep responsibilities separated

Foundation models do not own network access, credentials, provider selection,
filesystem sandboxes, encryption, or retention. Those controls belong to the
runtime or deploying application. Optional integrations should fail with the
typed missing-dependency error rather than changing behavior silently or
installing code during execution.

Use `OperationRefusal` when a requested conversion would be unsafe, unsupported,
or lossy. Do not coerce a value to satisfy a consumer, discard units, erase
unknown provenance, or convert a refusal into an empty successful payload.
Warnings on degraded success must remain attached through serialization and
downstream transport.

When a suspicious payload is found, preserve its bytes outside normal output,
record a redacted validation envelope and content fingerprint, and prevent it
from entering caches or migration output. Recovery should create a validated
derived document with provenance back to the quarantined source, never rewrite
the source in place.
