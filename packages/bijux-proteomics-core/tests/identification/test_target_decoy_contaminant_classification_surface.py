# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import (
    PsmRecord,
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
    classify_target_decoy_contaminant,
    export_psm_tsv,
    is_biological_foreground_class,
)


def test_unified_classification_distinguishes_target_decoy_and_contaminant_cases() -> (
    None
):
    target = classify_target_decoy_contaminant(
        protein_refs=("P11111",),
        target_decoy_label="target",
    )
    decoy = classify_target_decoy_contaminant(
        protein_refs=("DECOY_P11111",),
    )
    contaminant = classify_target_decoy_contaminant(
        protein_refs=("CON__KERATIN",),
    )
    mixed = classify_target_decoy_contaminant(
        protein_refs=("CON__TRYP_PIG", "P11111"),
    )

    assert target.target_decoy_contaminant_class is TargetDecoyContaminantClass.TARGET
    assert target.target_decoy_label is TargetDecoyLabel.TARGET
    assert target.contaminant_flag is False

    assert decoy.target_decoy_contaminant_class is TargetDecoyContaminantClass.DECOY
    assert decoy.target_decoy_label is TargetDecoyLabel.DECOY
    assert decoy.contaminant_flag is False

    assert (
        contaminant.target_decoy_contaminant_class
        is TargetDecoyContaminantClass.CONTAMINANT
    )
    assert contaminant.target_decoy_label is TargetDecoyLabel.TARGET
    assert contaminant.contaminant_flag is True

    assert mixed.target_decoy_contaminant_class is TargetDecoyContaminantClass.MIXED
    assert mixed.target_decoy_label is TargetDecoyLabel.TARGET
    assert mixed.contaminant_flag is True


def test_unified_classification_treats_decoy_contaminant_conflicts_as_mixed() -> None:
    classification = classify_target_decoy_contaminant(
        protein_refs=("CON__P54321",),
        target_decoy_label="decoy",
        explicit_contaminant_label="contaminant",
    )

    assert classification.target_decoy_label is TargetDecoyLabel.DECOY
    assert classification.contaminant_flag is True
    assert (
        classification.target_decoy_contaminant_class
        is TargetDecoyContaminantClass.MIXED
    )


def test_psm_record_derives_unified_class_from_compatibility_fields() -> None:
    contaminant = PsmRecord(
        spectrum_id="scan-contaminant",
        peptide="KERATINP",
        canonical_peptide="KERATINP",
        charge=2,
        score=98.0,
        protein_refs=("CON__KERATIN",),
        target_decoy_label=TargetDecoyLabel.TARGET,
    )
    mixed = PsmRecord(
        spectrum_id="scan-mixed",
        peptide="TRYPSINP",
        canonical_peptide="TRYPSINP",
        charge=2,
        score=96.0,
        protein_refs=("CON__TRYP_PIG", "P11111"),
        target_decoy_label=TargetDecoyLabel.TARGET,
    )

    assert (
        contaminant.target_decoy_contaminant_class
        is TargetDecoyContaminantClass.CONTAMINANT
    )
    assert mixed.target_decoy_contaminant_class is TargetDecoyContaminantClass.MIXED
    assert (
        is_biological_foreground_class(contaminant.target_decoy_contaminant_class)
        is False
    )
    assert is_biological_foreground_class(mixed.target_decoy_contaminant_class) is False
    assert is_biological_foreground_class(TargetDecoyContaminantClass.TARGET) is True


def test_psm_tsv_export_includes_unified_class_column(tmp_path: Path) -> None:
    path = tmp_path / "psms.tsv"
    export_psm_tsv(
        (
            PsmRecord(
                spectrum_id="scan-1",
                peptide="PEPTIDE",
                canonical_peptide="PEPTIDE",
                charge=2,
                score=100.0,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
            PsmRecord(
                spectrum_id="scan-2",
                peptide="KERATINP",
                canonical_peptide="KERATINP",
                charge=2,
                score=90.0,
                protein_refs=("CON__KERATIN",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        ),
        path,
    )

    rendered = path.read_text(encoding="utf-8")

    assert "target_decoy_contaminant_class" in rendered.splitlines()[0]
    assert "\tcontaminant\ttrue" in rendered
