---
title: Observability and Diagnostics
audience: developer
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Observability and Diagnostics

Foundation is an in-process contract library, not an execution service. It does
not own dashboards, request tracing, or a logging backend. Its observability
surface is the deterministic information returned by validation, compatibility,
serialization, refusal, and result contracts. Calling applications decide where
that information is logged and how it is correlated with a run.

## Diagnostic layers

| Layer | Inspect | Interpretation |
| --- | --- | --- |
| Syntax | JSON decoder error and source location | The document cannot yet be treated as a foundation payload. |
| Shape | Model validation locations, expected types, and rejected extra fields | The payload does not satisfy the selected contract. |
| Compatibility | Found version, expected version, compatibility assessment, and migration path | The shape may be valid for a different contract generation. |
| Identity | Hash policy, fingerprint scope, and expected versus observed digest | Canonical content changed or was hashed under a different policy. |
| Outcome | Support state, refusal kind, error category, warnings, and recoverability | The operation completed, degraded, refused, or failed. |
| Provenance | Locator kind, URI, label, fingerprint, and attributes | The result can be traced to a source or derived artifact. |

Preserve field locations from model-validation errors. “Contract invalid” is
not actionable when the real issue is an unknown key, an invalid identifier, or
a unit-bearing value outside its allowed representation. For migrations,
record every `from_version` and `to_version` edge that ran. For hashes, record
the active algorithm and canonicalization policy rather than only the digest.

## Correlate without changing contracts

Add run identifiers, request identifiers, timestamps, and deployment metadata
in the caller's event envelope. Do not insert operational metadata into a
scientific document merely to improve logs: doing so changes its canonical
serialization and fingerprint. Use `ProvenancePointer` for durable source
relationships and keep ephemeral correlation fields outside the governed
payload unless its schema explicitly owns them.

A useful incident record contains the contract type, package and contract
version, operation, error or refusal code, recoverability, redacted validation
details, provenance pointer, and fingerprint policy. Avoid logging complete
scientific payloads by default. The smallest failing field set plus a stable
fingerprint usually provides stronger correlation with less data exposure.

Diagnostics are sufficient when another consumer can distinguish malformed
input, incompatible versioning, failed migration, changed identity, and an
intentional refusal without reproducing the original environment.
