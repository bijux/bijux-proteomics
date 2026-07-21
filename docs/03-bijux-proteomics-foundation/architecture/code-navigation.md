---
title: Code Navigation
audience: developer
type: architecture
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Code Navigation

Bijux Proteomics Foundation is the repository’s contract kernel. Its small tree
owns only meanings that must remain identical across multiple packages:
identifiers, deterministic JSON, schema evolution, provenance, support states,
and structured outcomes.

## Fast reading route

1. Start at `public_api.py`. The machine-readable root ledger names every
   permitted package-root export, its capability class, owner module, and reason
   it is shared. The root budget intentionally limits the facade.
2. Read `identity/identifiers.py` for `ProgramId`, `TargetId`, `CandidateId`,
   `EvidenceId`, `ClaimId`, `GateId`, `AssayId`, and `BatchId`. These are the
   identity vocabulary joining higher packages.
3. Read `serialization/json_contracts.py` and `canonical_json.py` for the model
   base, deterministic encoding, loading, dumping, and fingerprints.
4. Continue through `document_schema.py`, `scientific_values.py`,
   `stable_hashes.py`, `fingerprints.py`, and `stable_values.py` for versioned
   envelopes, units and ranges, hashing policies, typed fingerprint scopes, and
   deterministic ordering.
5. Read `compatibility/schema_versions.py`, `schema_assessments.py`, and
   `schema_migrations.py` together. They distinguish compatibility judgment from
   explicit transformation.
6. Read `outcomes/` for exception categories, optional-dependency failures,
   error envelopes, refusals, and success/degraded/refused result invariants.
7. Read `support/provenance.py` and `support/states.py` for cross-package source
   pointers and the shared support vocabulary.

## Question-to-owner map

| Question | Owner |
| --- | --- |
| Which identifier type crosses packages? | `identity/identifiers.py` |
| How is a model encoded or fingerprinted? | `serialization/json_contracts.py` and `canonical_json.py` |
| What metadata travels with a document? | `serialization/document_schema.py` |
| Is another schema version acceptable? | `compatibility/schema_assessments.py` |
| How does old data become current data? | `compatibility/schema_migrations.py` |
| How is an unsafe request refused? | `outcomes/refusals.py` and `outcomes/results.py` |
| How is a source or derived artifact located? | `support/provenance.py` |
| Why is a symbol exported at package root? | `public_api.py` |

## Avoid false owners

The `testing/` family contains reusable repository test policies and helpers;
it does not define scientific behavior. Package alias modules preserve import
compatibility; they do not authorize new root exports. `support/charter.py`
audits ownership and boundaries but does not replace the contracts it describes.

When a question involves peptide chemistry, evidence trust, recommendation
policy, execution, or lab operations, stop here and move to the owning package.
Foundation can carry the identifier, provenance, or outcome shape, but it must
not decide the domain meaning.
