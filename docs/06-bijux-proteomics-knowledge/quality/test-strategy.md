---
title: Test Strategy
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Test strategy

Knowledge testing applies pressure to evidence custody: incomplete sources,
ambiguous identities, duplicated lineage, contradiction, stale records,
unresolved review, serialization, and downstream interpretation.

## Evidence layers

| Layer | Contract under test | Representative suite |
| --- | --- | --- |
| reference custody | registry integrity, source identity, citation, license and freshness fields | `tests/references/` |
| biological identity | exact, ambiguous, absent, obsolete, cross-species, isoform, and namespace mapping | identity and biological namespace tests |
| claim and evidence models | valid/invalid construction, context, provenance, confidence meaning, and immutability | `tests/memory/test_claims.py`, `test_evidence_bundle.py` |
| graph integrity | endpoints, edge types, support, contradiction, orphan prevention, and round trip | `test_evidence_graph.py` |
| reconciliation | competing contexts, deterministic policy, hold, unresolved, and audit trace | `test_resolution.py` and contradiction surfaces |
| review state | fixed revision, complete adverse evidence, disposition, rationale, and stable assembly | `tests/reviews/` |
| grounding | citations, benchmark lineage, literature coverage, deficits, contradiction, and release ceiling | workflow grounding and literature tests |
| package boundary | Foundation serialization, Core results, Intelligence references, and Lab feedback remain aligned | `tests/package/` and consumer tests |

## Challenge route

```mermaid
flowchart LR
    R["source and identity"] --> M["claim and evidence models"]
    M --> G["graph integrity"]
    G --> C["contradiction and reconciliation"]
    C --> V["review revision"]
    V --> B["consumer bundle"]
```

Run the focused source, memory, review, or grounding suite first, then the full
package suite for shared models, persistence, registries, and public outputs:

```bash
uv run --project packages/bijux-proteomics-knowledge \
  pytest -q packages/bijux-proteomics-knowledge/tests
```

## Required imperfect evidence

Include missing sources, duplicate lineage, ambiguous identifiers, stale
records, unsupported namespaces, conflicting claims, context-dependent
agreement, unresolved reconciliation, and incomplete review. An idealized
single-source graph cannot establish honest uncertainty handling.

Fixture replay proves deterministic handling of retained records. Live-source
availability and freshness require separate retrieval evidence. Keep those
claims distinct in test reports.
