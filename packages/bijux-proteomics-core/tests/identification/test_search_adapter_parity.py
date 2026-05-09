# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.contracts import (
    PsmParseReport,
    PsmRecord,
    TargetDecoyLabel,
)
from bijux_proteomics.identification.search_adapter_loss import (
    build_search_adapter_parity_report,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    build_search_result_family_policy,
    get_search_adapter_manifest,
)


def test_search_adapter_parity_report_accepts_release_ready_normalization() -> None:
    manifest = get_search_adapter_manifest(SearchAdapterKind.SAGE)
    assert manifest.mapping is not None
    normalized_record = PsmRecord(
        spectrum_id="sage-1",
        peptide="PEPTIDE",
        canonical_peptide="PEPTIDE",
        charge=2,
        score=15.0,
        q_value=0.002,
        protein_refs=("P12345",),
        target_decoy_label=TargetDecoyLabel.TARGET,
    )
    report = SearchAdapterNormalizationReport(
        adapter_manifest=manifest,
        family_policy=build_search_result_family_policy(manifest),
        source_columns=(
            "scannr",
            "peptide",
            "charge",
            "discriminant_score",
            "proteins",
            "label",
            "q_value",
        ),
        parse_report=PsmParseReport(
            total_rows=1,
            accepted_records=(normalized_record,),
            column_mapping=manifest.mapping,
        ),
        normalized_records=(normalized_record,),
        evidence_rows=(),
    )

    parity = build_search_adapter_parity_report(report)

    assert parity.release_acceptable is True
    assert parity.failing_criteria == ()


def test_search_adapter_parity_report_refuses_material_information_loss() -> None:
    manifest = get_search_adapter_manifest(SearchAdapterKind.SAGE)
    assert manifest.mapping is not None
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

    parity = build_search_adapter_parity_report(normalization_report)

    assert parity.release_acceptable is False
    assert "imported_semantics" in parity.failing_criteria
    assert "loss_accounting" in parity.failing_criteria
    assert "confidence_normalization" in parity.failing_criteria
