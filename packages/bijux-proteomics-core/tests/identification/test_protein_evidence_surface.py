# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

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
from bijux_proteomics_foundation import JsonModel

from .test_identification_surface import _default_mapping, _psm_fixture


class ProteinEvidenceReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    high_q_value: float = Field(..., ge=0.0)
    moderate_q_value: float = Field(..., ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    run_contexts: tuple[RunDetectionContext, ...] = Field(default_factory=tuple)
    expected_entries: tuple[dict[str, object], ...] = Field(default_factory=tuple)


def _reference_case() -> ProteinEvidenceReferenceCase:
    fixture = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "identification"
        / "protein_evidence_reference_cases.json"
    )
    return ProteinEvidenceReferenceCase.model_validate(
        json.loads(fixture.read_text(encoding="utf-8"))[0]
    )


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
    exact = build_protein_evidence_report(
        case.records,
        high_q_value=case.high_q_value,
        moderate_q_value=case.moderate_q_value,
        score_orientation=case.score_orientation,
        run_contexts=case.run_contexts,
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

    report = build_protein_evidence_report(
        case.records,
        high_q_value=case.high_q_value,
        moderate_q_value=case.moderate_q_value,
        score_orientation=case.score_orientation,
        run_contexts=case.run_contexts,
    )

    summary_tsv = render_protein_evidence_summary_tsv(report)
    entries_tsv = render_protein_evidence_entries_tsv(report)

    assert "high_confidence_count\t1" in summary_tsv
    assert "ambiguous_count\t1" in summary_tsv
    assert "shared_peptide_only_count\t1" in summary_tsv
    assert "reproducibility_hash" in summary_tsv
    assert "P33333;P44444" in entries_tsv
    assert "\tambiguous\tshared_peptide_only\t" in entries_tsv
