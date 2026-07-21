---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Domain Language

Foundation terminology describes cross-package contracts without claiming scientific interpretation.

| Term | Meaning |
| --- | --- |
| **typed identifier** | A validated identifier whose type communicates the entity it names, such as a program, claim, assay, or artifact |
| **JSON contract** | A typed model with explicit validation and a stable JSON-compatible representation |
| **document schema** | Metadata describing version, producer, lineage, lifecycle state, and revision for a durable document |
| **canonical JSON** | The unique supported JSON encoding used for comparison and hashing |
| **stable value** | A value normalized so equivalent logical inputs do not vary by incidental Python representation |
| **content hash** | A digest of canonical content used to detect change or corruption |
| **fingerprint** | A stable identity derived from the contract-relevant content of a model or payload |
| **schema version** | The normalized version of a persisted document shape, independent of the package release version |
| **compatibility assessment** | A determination made before reading or migrating a document across schema versions |
| **schema migration** | A declared transformation between known document shapes |
| **import migration** | Compatibility routing from a historical Python import path to its supported owner |
| **failure** | A machine-readable account of an operation that could not satisfy its contract |
| **refusal** | An intentional decision not to proceed because declared preconditions or policy are unmet |
| **provenance** | The identities and relationships needed to trace a document or result to its inputs and producer |

“Canonical” means deterministic under the declared contract; it does not mean scientifically correct. A stable hash proves content identity, not truth. Likewise, schema compatibility proves that a document can be interpreted structurally, not that its evidence is adequate for a decision.

Scientific concepts belong in core, evidence authority in knowledge, decision policy in intelligence, experimental operations in lab, and execution state in runtime. Foundation gives those packages a shared grammar without absorbing their meanings.
