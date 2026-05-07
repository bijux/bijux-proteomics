# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.contracts import (
    PsmParseReport,
    PsmRecord,
    TargetDecoyLabel,
)
from bijux_proteomics.identification.search_adapter_loss import (
    build_protein_inference_engine_disagreement_dossier,
    build_search_adapter_information_loss_report,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    build_search_result_family_policy,
    get_search_adapter_manifest,
    normalize_search_results_with_adapter,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "search_adapters" / name


def test_search_adapter_information_loss_report_flags_material_missing_fields() -> None:
    manifest = get_search_adapter_manifest(SearchAdapterKind.SAGE)
    normalization_report = SearchAdapterNormalizationReport(
        adapter_manifest=manifest,
        family_policy=build_search_result_family_policy(manifest),
        source_columns=("scannr", "peptide", "charge", "discriminant_score", "label"),
        parse_report=PsmParseReport(
            total_rows=1,
            accepted_records=(
                PsmRecord(
                    spectrum_id="sage-1",
                    peptide="PEPTIDE",
                    canonical_peptide="PEPTIDE",
                    charge=2,
                    score=15.0,
                    q_value=0.002,
                    protein_refs=(),
                    target_decoy_label=TargetDecoyLabel.TARGET,
                ),
            ),
            column_mapping=manifest.mapping,
        ),
        normalized_records=(),
        evidence_rows=(),
    )

    loss_report = build_search_adapter_information_loss_report(normalization_report)

    assert loss_report.acceptable_for_identification_claims is False
    assert "proteins" in loss_report.material_lost_columns
    assert "q_value" in loss_report.material_lost_columns


def test_protein_inference_engine_disagreement_dossier_tracks_strategy_divergence() -> None:
    comet = normalize_search_results_with_adapter(
        source_path=_fixture("comet_merge.tsv"),
        adapter_kind=SearchAdapterKind.COMET,
    )
    sage = normalize_search_results_with_adapter(
        source_path=_fixture("sage_merge.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )

    dossier = build_protein_inference_engine_disagreement_dossier((comet, sage))

    assert dossier.material_disagreement_count >= 1
    assert any(entry.strategy_label == "grouped" for entry in dossier.entries)
