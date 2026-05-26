# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPack,
    AnnotationPackSummary,
    load_annotation_pack,
    render_annotation_pack_json,
)
from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    BiologicalContextRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics_knowledge.drugs.targets import (
    DrugTargetRelationshipType,
    DrugTargetResolutionEntry,
    render_drug_target_resolution_tsv,
    resolve_drug_targets,
)


def test_resolve_drug_targets_keeps_pathway_neighbors_out_of_direct_targets() -> None:
    report = resolve_drug_targets(
        ("EGFR", "ERBB2", "STAT3"),
        _annotation_pack(),
    )

    assert report.entries == (
        DrugTargetResolutionEntry(
            protein_id="EGFR",
            drug="Erlotinib",
            relationship_type=DrugTargetRelationshipType.DIRECT_TARGET,
            direct_target=True,
            annotation_source="DrugBank:DB00530",
        ),
        DrugTargetResolutionEntry(
            protein_id="ERBB2",
            drug="Erlotinib",
            relationship_type=DrugTargetRelationshipType.INDIRECT_PATHWAY_NEIGHBOR,
            direct_target=False,
            annotation_source="DrugBank:DB00530",
        ),
    )
    assert report.summary.protein_count == 3
    assert report.summary.resolved_protein_count == 2
    assert report.summary.drug_count == 1
    assert report.summary.direct_target_count == 1
    assert report.summary.indirect_pathway_neighbor_count == 1


def test_resolve_drug_targets_renders_stable_tsv_rows() -> None:
    report = resolve_drug_targets(
        ("P00533", "Q15303"),
        _annotation_pack(),
    )

    rendered = render_drug_target_resolution_tsv(report.entries)

    assert rendered.splitlines() == [
        "protein_id\tdrug\trelationship_type\tdirect_target\tannotation_source",
        "P00533\tErlotinib\tdirect_target\ttrue\tDrugBank:DB00530",
        "Q15303\tErlotinib\tindirect_pathway_neighbor\tfalse\tDrugBank:DB00530",
    ]


def test_resolve_drug_targets_round_trips_exported_annotation_pack(
    tmp_path: Path,
) -> None:
    original_pack = _annotation_pack()
    exported_path = tmp_path / "drug_annotation_pack.json"
    exported_path.write_text(
        render_annotation_pack_json(original_pack),
        encoding="utf-8",
    )
    reloaded_pack = load_annotation_pack(exported_path)

    original_report = resolve_drug_targets(
        ("EGFR", "ERBB2", "STAT3"),
        original_pack,
    )
    reloaded_report = resolve_drug_targets(
        ("EGFR", "ERBB2", "STAT3"),
        reloaded_pack,
    )

    assert reloaded_report == original_report


def _annotation_pack() -> AnnotationPack:
    return AnnotationPack(
        source_path="test-drug-pack.json",
        pack_name="drug-target-test-pack",
        protein_features=(
            ProteinAnnotationRecord(
                protein_ref="P00533",
                gene_symbol="EGFR",
                description="epidermal growth factor receptor",
            ),
            ProteinAnnotationRecord(
                protein_ref="Q15303",
                gene_symbol="ERBB2",
                description="erb-b2 receptor tyrosine kinase 2",
            ),
        ),
        drug_targets=(
            BiologicalContextRecord(
                protein_ref="P00533",
                context_kind=BiologicalContextKind.DRUG_TARGET,
                context_id="drug:erlotinib",
                context_name="Erlotinib",
                source_name="DrugBank",
                source_accession="DrugBank:DB00530",
                evidence="approved direct inhibitor",
            ),
            BiologicalContextRecord(
                protein_ref="Q15303",
                context_kind=BiologicalContextKind.DRUG_TARGET,
                context_id="drug:erlotinib",
                context_name="Erlotinib",
                source_name="DrugBank",
                source_accession="DrugBank:DB00530",
                evidence="pathway neighbor support",
                metadata={"relationship_type": "pathway_neighbor"},
            ),
        ),
        summary=AnnotationPackSummary(
            protein_feature_count=2,
            pathway_count=0,
            complex_count=0,
            compartment_count=0,
            drug_target_count=2,
            disease_term_count=0,
            kinase_substrate_count=0,
            ortholog_count=0,
        ),
    )
