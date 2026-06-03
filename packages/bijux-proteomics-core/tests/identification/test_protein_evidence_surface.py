# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.cross_run_reproducibility import (
    RunDetectionContext,
)
from bijux_proteomics.identification.protein_evidence import (
    ProteinEvidenceDowngradeReason,
    ProteinEvidenceTier,
    build_protein_evidence_report,
    render_protein_evidence_entries_tsv,
    render_protein_evidence_summary_tsv,
)
from bijux_proteomics.identification.search_adapters import parse_psm_tsv

from .test_identification_surface import _default_mapping, _psm_fixture


def _reference_case() -> dict[str, object]:
    fixture = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "identification"
        / "protein_evidence_reference_cases.json"
    )
    return json.loads(fixture.read_text(encoding="utf-8"))[0]


def test_protein_evidence_report_counts_exact_owned_tiers() -> None:
    records = tuple(
        parse_psm_tsv(
            _psm_fixture("protein_inference_results.tsv"),
            mapping=_default_mapping(),
        ).accepted_records
    )

    report = build_protein_evidence_report(records)

    ambiguous = next(
        entry for entry in report.entries if entry.protein_refs == ("P22222", "P44444")
    )

    assert ambiguous.evidence_tier is ProteinEvidenceTier.AMBIGUOUS
    assert (
        ProteinEvidenceDowngradeReason.SHARED_PEPTIDE_ONLY
        in ambiguous.downgrade_reasons
    )

    case = _reference_case()
    reference_records = tuple(
        PsmRecord.model_validate(record) for record in case["records"]
    )
    run_contexts = tuple(
        RunDetectionContext.model_validate(context) for context in case["run_contexts"]
    )
    exact = build_protein_evidence_report(
        reference_records,
        high_q_value=case["high_q_value"],
        moderate_q_value=case["moderate_q_value"],
        score_orientation=case["score_orientation"],
        run_contexts=run_contexts,
    )

    assert exact.summary.total_groups == 6
    assert exact.summary.high_confidence_count == 1
    assert exact.summary.moderate_count == 1
    assert exact.summary.weak_count == 1
    assert exact.summary.ambiguous_count == 1
    assert exact.summary.contaminant_count == 1
    assert exact.summary.decoy_count == 1


def test_protein_evidence_renderers_preserve_tier_and_reason_ledgers() -> None:
    case = _reference_case()
    records = tuple(PsmRecord.model_validate(record) for record in case["records"])
    run_contexts = tuple(
        RunDetectionContext.model_validate(context) for context in case["run_contexts"]
    )

    report = build_protein_evidence_report(
        records,
        high_q_value=case["high_q_value"],
        moderate_q_value=case["moderate_q_value"],
        score_orientation=case["score_orientation"],
        run_contexts=run_contexts,
    )

    summary_tsv = render_protein_evidence_summary_tsv(report)
    entries_tsv = render_protein_evidence_entries_tsv(report)

    assert "high_confidence_count\t1" in summary_tsv
    assert "ambiguous_count\t1" in summary_tsv
    assert "shared_peptide_only_count\t1" in summary_tsv
    assert "reproducibility_hash" in summary_tsv
    assert "P33333;P44444" in entries_tsv
    assert "\tambiguous\tshared_peptide_only\t" in entries_tsv
