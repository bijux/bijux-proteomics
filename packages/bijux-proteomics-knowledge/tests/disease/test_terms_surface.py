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
from bijux_proteomics_knowledge.disease.terms import (
    DiseaseTermResolutionEntry,
    render_disease_term_resolution_tsv,
    resolve_disease_terms,
)


def test_resolve_disease_terms_requires_explicit_source_annotation() -> None:
    report = resolve_disease_terms(
        ("P04637", "P28482", "UNMAPPED1"),
        _disease_pack(),
    )

    assert report.entries == (
        DiseaseTermResolutionEntry(
            protein_id="P04637",
            term_id="DOID:162",
            term_name="cancer",
            source="Disease Ontology",
            evidence_type="disease_term",
        ),
        DiseaseTermResolutionEntry(
            protein_id="P28482",
            term_id="HP:0001250",
            term_name="seizures",
            source="HPO",
            evidence_type="phenotype_term",
        ),
    )
    assert report.summary.protein_count == 3
    assert report.summary.resolved_protein_count == 2
    assert report.summary.term_count == 2
    assert report.summary.disease_term_count == 1
    assert report.summary.phenotype_term_count == 1
    assert report.summary.source_filtered_row_count == 1


def test_resolve_disease_terms_renders_stable_tsv_rows() -> None:
    report = resolve_disease_terms(
        ("P04637", "P28482"),
        _disease_pack(),
    )

    rendered = render_disease_term_resolution_tsv(report.entries)

    assert rendered.splitlines() == [
        "protein_id\tterm_id\tterm_name\tsource\tevidence_type",
        "P04637\tDOID:162\tcancer\tDisease Ontology\tdisease_term",
        "P28482\tHP:0001250\tseizures\tHPO\tphenotype_term",
    ]


def test_resolve_disease_terms_round_trips_exported_annotation_pack(
    tmp_path: Path,
) -> None:
    original_pack = _annotation_pack()
    exported_path = tmp_path / "disease_annotation_pack.json"
    exported_path.write_text(
        render_annotation_pack_json(original_pack),
        encoding="utf-8",
    )
    reloaded_pack = load_annotation_pack(exported_path)

    original_report = resolve_disease_terms(
        ("P04637", "P28482", "UNMAPPED1"),
        original_pack,
    )
    reloaded_report = resolve_disease_terms(
        ("P04637", "P28482", "UNMAPPED1"),
        reloaded_pack,
    )

    assert reloaded_report == original_report


def _disease_pack() -> tuple[BiologicalContextRecord, ...]:
    return (
        BiologicalContextRecord(
            protein_ref="P04637",
            context_kind=BiologicalContextKind.DISEASE_TERM,
            context_id="DOID:162",
            context_name="cancer",
            source_name="Disease Ontology",
        ),
        BiologicalContextRecord(
            protein_ref="P28482",
            context_kind=BiologicalContextKind.PHENOTYPE_TERM,
            context_id="HP:0001250",
            context_name="seizures",
            source_name="HPO",
        ),
        BiologicalContextRecord(
            protein_ref="P04637",
            context_kind=BiologicalContextKind.DISEASE_TERM,
            context_id="DOID:9999",
            context_name="unsourced disease row",
        ),
    )


def _annotation_pack() -> AnnotationPack:
    return AnnotationPack(
        source_path="test-disease-pack.json",
        pack_name="disease-term-test-pack",
        protein_features=(
            ProteinAnnotationRecord(
                protein_ref="P04637",
                gene_symbol="TP53",
                description="tumor protein p53",
            ),
            ProteinAnnotationRecord(
                protein_ref="P28482",
                gene_symbol="MAPK1",
                description="mitogen activated protein kinase 1",
            ),
        ),
        disease_terms=_disease_pack(),
        summary=AnnotationPackSummary(
            protein_feature_count=2,
            pathway_count=0,
            complex_count=0,
            compartment_count=0,
            drug_target_count=0,
            disease_term_count=3,
            kinase_substrate_count=0,
            ortholog_count=0,
        ),
    )
