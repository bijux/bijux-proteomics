# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab import (
    ContaminantAnnotationEntry,
    ContaminantClass,
    ContaminantEvidenceEntry,
    classify_contamination,
    render_contamination_classification_tsv,
)


def test_classify_contamination_distinguishes_keratin_enzyme_standard_and_unknown() -> (
    None
):
    rows = classify_contamination(
        (
            ContaminantEvidenceEntry(
                sample_id="sample_keratin",
                protein_ref="CON__K1C10_HUMAN",
                intensity=1200.0,
                sample_total_intensity=10_000.0,
            ),
            ContaminantEvidenceEntry(
                sample_id="sample_keratin",
                protein_ref="CON__K2C1_HUMAN",
                intensity=700.0,
                sample_total_intensity=10_000.0,
            ),
            ContaminantEvidenceEntry(
                sample_id="sample_enzyme",
                protein_ref="CON__TRYP_PIG",
                intensity=950.0,
                sample_total_intensity=10_000.0,
            ),
            ContaminantEvidenceEntry(
                sample_id="sample_standard",
                protein_ref="CON__ALBU_BOVIN",
                intensity=1600.0,
                sample_total_intensity=10_000.0,
            ),
            ContaminantEvidenceEntry(
                sample_id="sample_unknown",
                protein_ref="CON__Q9UNKNOWN",
                intensity=800.0,
                sample_total_intensity=10_000.0,
            ),
        ),
        (
            ContaminantAnnotationEntry(
                protein_ref="CON__K1C10_HUMAN",
                contaminant_class=ContaminantClass.KERATIN,
            ),
            ContaminantAnnotationEntry(
                protein_ref="CON__K2C1_HUMAN",
                contaminant_class=ContaminantClass.KERATIN,
            ),
            ContaminantAnnotationEntry(
                protein_ref="CON__TRYP_PIG",
                contaminant_class=ContaminantClass.ENZYME,
            ),
            ContaminantAnnotationEntry(
                protein_ref="CON__ALBU_BOVIN",
                contaminant_class=ContaminantClass.STANDARD,
            ),
        ),
    )
    lookup = {row.sample_id: row for row in rows}

    assert lookup["sample_keratin"].contaminant_class is ContaminantClass.KERATIN
    assert lookup["sample_enzyme"].contaminant_class is ContaminantClass.ENZYME
    assert lookup["sample_standard"].contaminant_class is ContaminantClass.STANDARD
    assert lookup["sample_unknown"].contaminant_class is ContaminantClass.UNKNOWN
    assert lookup["sample_keratin"].top_contaminant_proteins == (
        "CON__K1C10_HUMAN",
        "CON__K2C1_HUMAN",
    )


def test_classify_contamination_renders_tsv_and_mixed_source_action_hint() -> None:
    rows = classify_contamination(
        (
            ContaminantEvidenceEntry(
                sample_id="sample_mixed",
                protein_ref="CON__TRYP_PIG",
                intensity=900.0,
                sample_total_intensity=10_000.0,
            ),
            ContaminantEvidenceEntry(
                sample_id="sample_mixed",
                protein_ref="CON__K1C10_HUMAN",
                intensity=750.0,
                sample_total_intensity=10_000.0,
            ),
        ),
        (
            ContaminantAnnotationEntry(
                protein_ref="CON__TRYP_PIG",
                contaminant_class=ContaminantClass.ENZYME,
            ),
            ContaminantAnnotationEntry(
                protein_ref="CON__K1C10_HUMAN",
                contaminant_class=ContaminantClass.KERATIN,
            ),
        ),
    )
    rendered = render_contamination_classification_tsv(rows)

    assert rows[0].contaminant_class is ContaminantClass.MIXED
    assert "multiple contaminant sources" in rows[0].action_hint
    assert rendered.startswith(
        "sample_id\tcontaminant_class\ttop_contaminant_proteins\tintensity_fraction\taction_hint\n"
    )
    assert "sample_mixed" in rendered
