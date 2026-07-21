---
title: bijux-proteomics-knowledge
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# bijux-proteomics-knowledge

`bijux-proteomics-knowledge` is the scientific memory and grounding layer. It
records claims, evidence, provenance, context, and contradictions, and it
resolves proteomics results against biological entities without turning those
records into a recommendation policy.

```bash
python -m pip install bijux-proteomics-knowledge
```

## Evidence lifecycle

```mermaid
flowchart LR
    source["literature · ontology · database · run artifact"]
    normalize["normalize\nidentity · context · provenance"]
    memory["evidence memory\nrecords · claims · bundles"]
    reconcile["reconcile\nduplicates · conflicts · contradictions"]
    ground["ground\nprotein · pathway · feature · disease · drug"]
    assess["assess\ncoverage · sufficiency · risk"]
    brief["scientific review bundle"]
    source --> normalize --> memory --> reconcile --> ground --> assess --> brief
```

The package preserves disagreement. Contradictory evidence is not averaged
away, and missing context is not treated as negative evidence. Resolution
decisions retain their source and rule so they can be revisited.

## Public biological grounding

The curated root API exposes typed resolution reports and functions for:

- protein identifiers;
- protein feature overlaps;
- pathway membership and coverage confidence;
- protein-complex membership;
- kinase–substrate relationships;
- disease terms;
- drug–target relationships;
- cross-species orthologs;
- knowledge coverage and schema compatibility.

Each resolution family can render reviewable TSV output in addition to its
typed Python result. Root anchors `EvidenceRecord`, `EvidenceClaim`,
`EvidenceBundle`, and `KnowledgeDecisionBrief` connect those biological
resolutions to evidence memory and downstream review.

## Evidence and reference workflows

The deeper `references` surface provides citation and context grounding,
literature and ontology sources, curated corpora, benchmark ledgers, comparator
positions and failures, contradiction dossiers, evidence-sufficiency checks,
knowledge-deficit reports, scientific thresholds, reading packs, replay proof,
and release-facing narratives.

These workflows distinguish three questions:

1. **Was a source identified and represented correctly?**
2. **Does it support the claim in the declared context?**
3. **Is the assembled evidence sufficient for the intended use?**

A “yes” at one level does not imply a “yes” at the next.

## Memory integrity

Evidence memory uses explicit claim and evidence models, normalized ingestion,
reconciliation, and graph-integrity checks. Provenance links the normalized
record back to its source; contradiction handling records incompatible claims
without discarding either; review briefs summarize the current state without
becoming the canonical evidence store.

## Ownership boundary

Knowledge depends on foundation contracts and core scientific semantics. It
does not depend on runtime, intelligence, or lab. Runtime can provide a run
bundle as an input artifact; intelligence consumes the resulting scientific
review bundle; lab observations can be ingested as new evidence through an
explicit handoff. None of those consumers may mutate evidence history through
their own policy or operational state.

## Documentation map

- [Package overview](foundation/package-overview.md) maps memory, grounding,
  biological context, and review surfaces.
- [Workflow claim grounding](foundation/workflow-claim-grounding.md) traces
  public claims to support and contradiction.
- [Workflow literature audits](foundation/workflow-literature-audits.md)
  explains curated source pressure.
- [Architecture](architecture/index.md) covers memory and reconciliation
  boundaries.
- [Interfaces](interfaces/index.md) documents Python, data, and artifact
  contracts.
- [Known limitations](quality/known-limitations.md) records source, coverage,
  and inference limits.
