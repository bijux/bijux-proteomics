# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import ProteinInferenceStrategyKind
from bijux_proteomics.identification.protein_inference_benchmarks import (
    ProteinInferenceBenchmarkScenarioKind,
    build_core_protein_inference_benchmark_suite,
)
from bijux_proteomics_foundation import JsonModel


class ProteinInferenceBenchmarkReferenceAssessment(JsonModel):
    model_config = ConfigDict(extra="forbid")

    strategy_kind: ProteinInferenceStrategyKind
    selected_proteins: tuple[str, ...] = Field(default_factory=tuple)
    false_positive_proteins: tuple[str, ...] = Field(default_factory=tuple)
    missed_proteins: tuple[str, ...] = Field(default_factory=tuple)
    selected_missing_fasta_proteins: tuple[str, ...] = Field(default_factory=tuple)


class ProteinInferenceBenchmarkReferenceReport(JsonModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    scenario_kind: ProteinInferenceBenchmarkScenarioKind
    disagreement_count: int = Field(..., ge=0)
    ambiguity_should_be_visible: bool
    ambiguity_exposed: bool
    missing_fasta_pressure: bool
    assessments: tuple[ProteinInferenceBenchmarkReferenceAssessment, ...] = Field(
        default_factory=tuple
    )


class ProteinInferenceBenchmarkReferenceSummary(JsonModel):
    model_config = ConfigDict(extra="forbid")

    scenario_count: int = Field(..., ge=0)
    shared_peptide_scenario_count: int = Field(..., ge=0)
    isoform_scenario_count: int = Field(..., ge=0)
    homolog_family_scenario_count: int = Field(..., ge=0)
    contaminant_scenario_count: int = Field(..., ge=0)
    all_decoy_scenario_count: int = Field(..., ge=0)
    all_target_scenario_count: int = Field(..., ge=0)
    tied_score_scenario_count: int = Field(..., ge=0)
    missing_fasta_scenario_count: int = Field(..., ge=0)
    ambiguity_visible_scenario_count: int = Field(..., ge=0)
    hidden_ambiguity_scenario_count: int = Field(..., ge=0)


class ProteinInferenceBenchmarkReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    suite_id: str = Field(..., min_length=1)
    expected_summary: ProteinInferenceBenchmarkReferenceSummary
    expected_reports: tuple[ProteinInferenceBenchmarkReferenceReport, ...] = Field(
        default_factory=tuple
    )


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_protein_inference_benchmark_reference_cases_match_expected_outputs() -> None:
    raw_cases = json.loads(
        _identification_fixture(
            "protein_inference_benchmark_reference_cases.json"
        ).read_text(encoding="utf-8")
    )
    cases = tuple(
        ProteinInferenceBenchmarkReferenceCase.model_validate(case)
        for case in raw_cases
    )

    case = cases[0]
    suite = build_core_protein_inference_benchmark_suite()

    assert suite.scenario_count == case.expected_summary.scenario_count
    assert (
        suite.shared_peptide_scenario_count
        == case.expected_summary.shared_peptide_scenario_count
    )
    assert suite.isoform_scenario_count == case.expected_summary.isoform_scenario_count
    assert (
        suite.homolog_family_scenario_count
        == case.expected_summary.homolog_family_scenario_count
    )
    assert (
        suite.contaminant_scenario_count
        == case.expected_summary.contaminant_scenario_count
    )
    assert (
        suite.all_decoy_scenario_count == case.expected_summary.all_decoy_scenario_count
    )
    assert (
        suite.all_target_scenario_count
        == case.expected_summary.all_target_scenario_count
    )
    assert (
        suite.tied_score_scenario_count
        == case.expected_summary.tied_score_scenario_count
    )
    assert (
        suite.missing_fasta_scenario_count
        == case.expected_summary.missing_fasta_scenario_count
    )
    assert (
        suite.ambiguity_visible_scenario_count
        == case.expected_summary.ambiguity_visible_scenario_count
    )
    assert (
        suite.hidden_ambiguity_scenario_count
        == case.expected_summary.hidden_ambiguity_scenario_count
    )

    assert len(suite.reports) == len(case.expected_reports)
    for observed_report, expected_report in zip(
        suite.reports,
        case.expected_reports,
        strict=True,
    ):
        assert observed_report.scenario_id == expected_report.scenario_id
        assert observed_report.scenario_kind is expected_report.scenario_kind
        assert observed_report.disagreement_count == expected_report.disagreement_count
        assert (
            observed_report.ambiguity_should_be_visible
            is expected_report.ambiguity_should_be_visible
        )
        assert observed_report.ambiguity_exposed is expected_report.ambiguity_exposed
        assert (
            observed_report.missing_fasta_pressure
            is expected_report.missing_fasta_pressure
        )
        assert len(observed_report.method_assessments) == len(
            expected_report.assessments
        )
        for observed_assessment, expected_assessment in zip(
            observed_report.method_assessments,
            expected_report.assessments,
            strict=True,
        ):
            assert (
                observed_assessment.strategy_kind is expected_assessment.strategy_kind
            )
            assert (
                observed_assessment.selected_proteins
                == expected_assessment.selected_proteins
            )
            assert (
                observed_assessment.false_positive_proteins
                == expected_assessment.false_positive_proteins
            )
            assert (
                observed_assessment.missed_proteins
                == expected_assessment.missed_proteins
            )
            assert (
                observed_assessment.selected_missing_fasta_proteins
                == expected_assessment.selected_missing_fasta_proteins
            )
