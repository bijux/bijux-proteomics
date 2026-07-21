---
title: Entrypoints and Worked Examples
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Entrypoints and worked examples

The package root exposes evidence models and high-value biological resolution
functions. Specialized memory, reconciliation, reference, and review builders
remain in their owner modules. Knowledge has no standalone CLI or HTTP API.

## Create a contextual evidence bundle

```python
from bijux_proteomics_knowledge import EvidenceBundle, EvidenceRecord
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceExtractionMethod,
    EvidenceKind,
    EvidenceOrigin,
    EvidenceSourceType,
    EvidenceStrength,
    QuantitativeSupport,
)

record = EvidenceRecord(
    evidence_id="evidence:akt1-phospho-17",
    kind=EvidenceKind.PHOSPHOPROTEOMICS,
    title="AKT1 site signal after treatment",
    source="run-17 differential PTM result",
    source_type=EvidenceSourceType.LAB_ASSAY,
    origin=EvidenceOrigin.OBSERVED,
    extraction_method=EvidenceExtractionMethod.AUTOMATED_IMPORT,
    biological_system="treated human cell line",
    endpoint="site abundance",
    claim="AKT1 site abundance increased after treatment",
    related_targets=["target:akt1"],
    decision_tags=["mechanism-review"],
    quantitative_support=QuantitativeSupport(
        effect_size=1.4,
        q_value=0.008,
        replicate_count=3,
        site_localization_probability=0.97,
        scale_type="log2-ratio",
    ),
    confidence=0.88,
    strength=EvidenceStrength.SUPPORTING,
)

bundle = EvidenceBundle(
    bundle_id="evidence:akt1-review-bundle",
    target_id="target:akt1",
    records=[record],
)
print(bundle.to_stable_json())
```

The record is intentionally verbose: context and quantitative limitations are
part of the evidence, not optional commentary.

## Resolve protein identifiers

```python
from bijux_proteomics_knowledge import (
    render_protein_id_resolution_tsv,
    resolve_protein_ids,
)

# `annotation_pack` is a curated AnnotationPack from bijux-proteomics-core.
rows = resolve_protein_ids(("P31749", "AKT1", "unknown-protein"), annotation_pack)
print(render_protein_id_resolution_tsv(rows))
```

Inspect `resolution_status` and `ambiguity_count` before using a resolved
accession. An alias match can be biologically unsafe when multiple entries share
the same symbol.

## Resolve pathway coverage

```python
from bijux_proteomics_knowledge import (
    PathwayCoveragePolicy,
    resolve_pathway_members,
)

report = resolve_pathway_members(
    ("P31749", "P27361"),
    pathway_pack,
    policy=PathwayCoveragePolicy(minimum_coverage_fraction=0.6),
)
for entry in report.entries:
    print(entry.pathway_id, entry.coverage_fraction, entry.unresolved_inputs)
```

Coverage confidence describes curated member resolution only. Use core
quantitative evidence and an explicit interpretation policy to assess activity.

## Choose the next surface

- `memory.models` owns evidence, claims, lineage, dossiers, and knowledge state.
- `memory.integrity` owns graph structure and integrity validation.
- `memory.reconciliation` owns conflict resolution and escalation.
- root resolution functions own protein, feature, pathway, complex, kinase,
  drug, disease, ortholog, and coverage reports.
- `references` owns grounding rules, scientific literature, comparators,
  benchmarks, risk, and reproducibility packs.
- `reviews` owns provenance, contradiction stress, and decision briefs.

Persist the typed report and reference identity before handing any knowledge
artifact to intelligence or lab workflows.
