# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific benchmark surfaces for protein inference credibility."""

from __future__ import annotations

from enum import StrEnum
import math

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.confidence import (
    ProteinInferenceStrategyKind,
    compare_protein_inference_strategies,
)
from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics_foundation import JsonModel


class ProteinInferenceBenchmarkScenarioKind(StrEnum):
    """Pressure families that a protein-inference workflow must survive."""

    SHARED_PEPTIDE_HEAVY = "shared_peptide_heavy"
    ISOFORM_HEAVY = "isoform_heavy"
    HOMOLOG_FAMILY_HEAVY = "homolog_family_heavy"
    CONTAMINANT_HEAVY = "contaminant_heavy"
    ALL_DECOY = "all_decoy"
    ALL_TARGET = "all_target"
    TIED_SCORE = "tied_score"
    MISSING_FASTA_ENTRY = "missing_fasta_entry"


class ProteinInferenceBenchmarkScenario(JsonModel):
    """One truth-scored protein-inference benchmark scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    scenario_kind: ProteinInferenceBenchmarkScenarioKind
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_present_proteins: tuple[str, ...] = Field(default_factory=tuple)
    expected_absent_proteins: tuple[str, ...] = Field(default_factory=tuple)
    fasta_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    ambiguity_should_be_visible: bool = False
    note: str = Field(..., min_length=1)


class ProteinInferenceMethodAssessment(JsonModel):
    """Truth-scored assessment for one protein-inference strategy."""

    model_config = ConfigDict(extra="forbid")

    strategy_kind: ProteinInferenceStrategyKind
    strategy_label: str = Field(..., min_length=1)
    selected_proteins: tuple[str, ...] = Field(default_factory=tuple)
    true_positive_count: int = Field(..., ge=0)
    false_positive_count: int = Field(..., ge=0)
    false_negative_count: int = Field(..., ge=0)
    precision: float = Field(..., ge=0.0, le=1.0)
    precision_interval_low: float = Field(..., ge=0.0, le=1.0)
    precision_interval_high: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    recall_interval_low: float = Field(..., ge=0.0, le=1.0)
    recall_interval_high: float = Field(..., ge=0.0, le=1.0)
    false_positive_proteins: tuple[str, ...] = Field(default_factory=tuple)
    missed_proteins: tuple[str, ...] = Field(default_factory=tuple)
    selected_missing_fasta_proteins: tuple[str, ...] = Field(default_factory=tuple)
    trustworthy_for_review: bool
    trust_note: str = Field(..., min_length=1)


class ProteinInferenceBenchmarkReport(JsonModel):
    """Benchmark result over one protein-inference truth scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    scenario_kind: ProteinInferenceBenchmarkScenarioKind
    expected_present_proteins: tuple[str, ...] = Field(default_factory=tuple)
    expected_absent_proteins: tuple[str, ...] = Field(default_factory=tuple)
    fasta_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptide_pressure: bool
    isoform_pressure: bool
    homolog_family_pressure: bool
    contaminant_pressure: bool
    all_decoy_pressure: bool
    all_target_pressure: bool
    tied_score_pressure: bool
    missing_fasta_pressure: bool
    ambiguity_should_be_visible: bool
    ambiguity_exposed: bool
    method_assessments: tuple[ProteinInferenceMethodAssessment, ...] = Field(
        default_factory=tuple
    )
    disagreement_count: int = Field(..., ge=0)
    scenario_note: str = Field(..., min_length=1)


class ProteinInferenceBenchmarkSuiteReport(JsonModel):
    """Aggregate benchmark proof across multiple pressure scenarios."""

    model_config = ConfigDict(extra="forbid")

    reports: tuple[ProteinInferenceBenchmarkReport, ...] = Field(default_factory=tuple)
    covered_strategy_kinds: tuple[ProteinInferenceStrategyKind, ...] = Field(
        default_factory=tuple
    )
    scenario_ids: tuple[str, ...] = Field(default_factory=tuple)
    scenario_kinds: tuple[ProteinInferenceBenchmarkScenarioKind, ...] = Field(
        default_factory=tuple
    )
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
    worst_precision_lower_bound: float = Field(..., ge=0.0, le=1.0)
    worst_recall_lower_bound: float = Field(..., ge=0.0, le=1.0)
    scenario_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class PickedGroupBenchmarkPressure(StrEnum):
    """Scenario families required before picked-group claims can travel."""

    DECOY_PAIRED_GROUPS = "decoy_paired_groups"
    SHARED_PEPTIDE_GROUPS = "shared_peptide_groups"
    ISOFORM_COLLISIONS = "isoform_collisions"
    CONTAMINANT_GROUP_PRESSURE = "contaminant_group_pressure"


class PickedGroupFdrBenchmarkScenarioPlan(JsonModel):
    """One required benchmark scenario for a future picked-group FDR claim."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    pressure: PickedGroupBenchmarkPressure
    scientific_question: str = Field(..., min_length=1)
    blocked_claim: str = Field(..., min_length=1)


class PickedGroupFdrBenchmarkPlan(JsonModel):
    """Explicit benchmark plan for picked-group FDR support."""

    model_config = ConfigDict(extra="forbid")

    claim_ready: bool
    current_state: str = Field(..., min_length=1)
    required_scenarios: tuple[PickedGroupFdrBenchmarkScenarioPlan, ...] = Field(
        default_factory=tuple
    )
    blocked_by: tuple[str, ...] = Field(default_factory=tuple)
    next_artifacts: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowTrustCriterionResult(JsonModel):
    """One criterion inside a workflow-claim trust rubric."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(..., min_length=1)
    passed: bool
    detail: str = Field(..., min_length=1)


class IdentificationWorkflowClaimReview(JsonModel):
    """Trust-rubric review for promoting an identification workflow claim."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    accepted: bool
    trust_score: float = Field(..., ge=0.0, le=1.0)
    precision_floor: float = Field(..., ge=0.0, le=1.0)
    recall_floor: float = Field(..., ge=0.0, le=1.0)
    criteria: tuple[WorkflowTrustCriterionResult, ...] = Field(default_factory=tuple)
    refusal_reasons: tuple[str, ...] = Field(default_factory=tuple)


def _wilson_interval(
    successes: int, total: int, *, z: float = 1.96
) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    proportion = successes / total
    denominator = 1.0 + (z * z) / total
    centre = proportion + (z * z) / (2.0 * total)
    margin = z * math.sqrt(
        (proportion * (1.0 - proportion) / total) + ((z * z) / (4.0 * total * total))
    )
    low = max(0.0, (centre - margin) / denominator)
    high = min(1.0, (centre + margin) / denominator)
    return (low, high)


def _base_accession(protein_ref: str) -> str:
    token = (
        protein_ref.removeprefix("DECOY_").removeprefix("REV__").removeprefix("CON__")
    )
    if "-" in token:
        return token.split("-", maxsplit=1)[0]
    return token


def _has_tied_top_score(records: tuple[PsmRecord, ...]) -> bool:
    if not records:
        return False
    top_score = max(record.score for record in records)
    top_records = tuple(record for record in records if record.score == top_score)
    top_proteins = {
        protein_ref for record in top_records for protein_ref in record.protein_refs
    }
    return len(top_proteins) > 1


def _benchmark_record(
    *,
    spectrum_id: str,
    peptide: str,
    score: float,
    protein_refs: tuple[str, ...],
    q_value: float = 0.001,
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.TARGET,
) -> PsmRecord:
    return PsmRecord(
        spectrum_id=spectrum_id,
        peptide=peptide,
        canonical_peptide=peptide,
        charge=2,
        score=score,
        q_value=q_value,
        protein_refs=protein_refs,
        target_decoy_label=target_decoy_label,
    )


def build_core_protein_inference_benchmark_scenarios() -> tuple[
    ProteinInferenceBenchmarkScenario, ...
]:
    """Build the owned protein-inference benchmark catalog."""

    return (
        ProteinInferenceBenchmarkScenario(
            scenario_id="shared-peptide-pressure",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.SHARED_PEPTIDE_HEAVY,
            records=(
                _benchmark_record(
                    spectrum_id="s001",
                    peptide="ACDEFGK",
                    score=120.0,
                    protein_refs=("P11111",),
                ),
                _benchmark_record(
                    spectrum_id="s002",
                    peptide="SHAREDK",
                    score=115.0,
                    q_value=0.002,
                    protein_refs=("P11111", "P22222"),
                ),
                _benchmark_record(
                    spectrum_id="s003",
                    peptide="MNPQRST",
                    score=110.0,
                    q_value=0.003,
                    protein_refs=("P33333",),
                ),
            ),
            expected_present_proteins=("P11111", "P33333"),
            expected_absent_proteins=("P22222",),
            fasta_protein_refs=("P11111", "P22222", "P33333"),
            ambiguity_should_be_visible=True,
            note="One absent protein is attractive only because it borrows shared-peptide support.",
        ),
        ProteinInferenceBenchmarkScenario(
            scenario_id="isoform-pressure",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.ISOFORM_HEAVY,
            records=(
                _benchmark_record(
                    spectrum_id="i001",
                    peptide="MELTIK",
                    score=130.0,
                    protein_refs=("P55555-1",),
                ),
                _benchmark_record(
                    spectrum_id="i002",
                    peptide="SHAREDIS",
                    score=118.0,
                    q_value=0.002,
                    protein_refs=("P55555-1", "P55555-2"),
                ),
            ),
            expected_present_proteins=("P55555-1",),
            expected_absent_proteins=("P55555-2",),
            fasta_protein_refs=("P55555-1", "P55555-2"),
            note="Isoform-specific evidence should keep the silent sibling isoform out.",
        ),
        ProteinInferenceBenchmarkScenario(
            scenario_id="homolog-family-pressure",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.HOMOLOG_FAMILY_HEAVY,
            records=(
                _benchmark_record(
                    spectrum_id="h001",
                    peptide="FAMILYK",
                    score=128.0,
                    protein_refs=("Q11111",),
                ),
                _benchmark_record(
                    spectrum_id="h002",
                    peptide="FAMILYSH",
                    score=116.0,
                    q_value=0.002,
                    protein_refs=("Q11111", "Q22222", "Q33333"),
                ),
            ),
            expected_present_proteins=("Q11111",),
            expected_absent_proteins=("Q22222", "Q33333"),
            fasta_protein_refs=("Q11111", "Q22222", "Q33333"),
            ambiguity_should_be_visible=True,
            note="Homolog-family sharing should not inflate silent family members into accepted proteins.",
        ),
        ProteinInferenceBenchmarkScenario(
            scenario_id="contaminant-pressure",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.CONTAMINANT_HEAVY,
            records=(
                _benchmark_record(
                    spectrum_id="c001",
                    peptide="TARGETAK",
                    score=126.0,
                    protein_refs=("P77777",),
                ),
                _benchmark_record(
                    spectrum_id="c002",
                    peptide="KERATIN",
                    score=119.0,
                    q_value=0.002,
                    protein_refs=("P77777", "CON__KERATIN1"),
                ),
            ),
            expected_present_proteins=("P77777",),
            expected_absent_proteins=("CON__KERATIN1",),
            fasta_protein_refs=("P77777", "CON__KERATIN1"),
            note="Contaminant-borrowed evidence must remain explicit instead of promoting the contaminant alongside the target.",
        ),
        ProteinInferenceBenchmarkScenario(
            scenario_id="all-decoy-input",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.ALL_DECOY,
            records=(
                _benchmark_record(
                    spectrum_id="d001",
                    peptide="DECADYK",
                    score=124.0,
                    protein_refs=("DECOY_P88888",),
                    target_decoy_label=TargetDecoyLabel.DECOY,
                ),
                _benchmark_record(
                    spectrum_id="d002",
                    peptide="DECOYQQ",
                    score=122.0,
                    q_value=0.002,
                    protein_refs=("DECOY_Q99999",),
                    target_decoy_label=TargetDecoyLabel.DECOY,
                ),
            ),
            expected_present_proteins=(),
            expected_absent_proteins=("DECOY_P88888", "DECOY_Q99999"),
            fasta_protein_refs=(),
            note="A decoy-only evidence table should not produce accepted biological proteins under any inference claim.",
        ),
        ProteinInferenceBenchmarkScenario(
            scenario_id="all-target-input",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.ALL_TARGET,
            records=(
                _benchmark_record(
                    spectrum_id="t001",
                    peptide="ANCHRPK",
                    score=125.0,
                    protein_refs=("P10101",),
                ),
                _benchmark_record(
                    spectrum_id="t002",
                    peptide="RIDGEPK",
                    score=112.0,
                    q_value=0.003,
                    protein_refs=("P20202",),
                ),
            ),
            expected_present_proteins=("P10101", "P20202"),
            expected_absent_proteins=(),
            fasta_protein_refs=("P10101", "P20202"),
            note="A target-only evidence table should preserve its supported proteins without inventing absent or decoy proteins.",
        ),
        ProteinInferenceBenchmarkScenario(
            scenario_id="tied-score-ambiguity",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.TIED_SCORE,
            records=(
                _benchmark_record(
                    spectrum_id="u001",
                    peptide="TIEDPEP",
                    score=121.0,
                    protein_refs=("P30303", "P40404"),
                ),
                _benchmark_record(
                    spectrum_id="u002",
                    peptide="TIEDALT",
                    score=121.0,
                    q_value=0.002,
                    protein_refs=("P30303", "P40404"),
                ),
            ),
            expected_present_proteins=("P30303", "P40404"),
            expected_absent_proteins=(),
            fasta_protein_refs=("P30303", "P40404"),
            ambiguity_should_be_visible=True,
            note="Exact tied-score proteins with only shared evidence should stay explicitly ambiguous instead of collapsing silently to one winner.",
        ),
        ProteinInferenceBenchmarkScenario(
            scenario_id="missing-fasta-entry",
            scenario_kind=ProteinInferenceBenchmarkScenarioKind.MISSING_FASTA_ENTRY,
            records=(
                _benchmark_record(
                    spectrum_id="m001",
                    peptide="FASTAOK",
                    score=123.0,
                    protein_refs=("P50505",),
                ),
                _benchmark_record(
                    spectrum_id="m002",
                    peptide="MISSINGF",
                    score=119.0,
                    q_value=0.002,
                    protein_refs=("P60606",),
                ),
            ),
            expected_present_proteins=("P50505",),
            expected_absent_proteins=("P60606",),
            fasta_protein_refs=("P50505",),
            ambiguity_should_be_visible=True,
            note="A protein supported by PSM rows but missing from the FASTA catalog must remain an explicit inference risk instead of blending into accepted output.",
        ),
    )


def build_protein_inference_benchmark_report(
    scenario: ProteinInferenceBenchmarkScenario,
    *,
    picked_threshold: float = 0.05,
) -> ProteinInferenceBenchmarkReport:
    """Truth-score multiple protein-inference strategies over one pressure scenario."""

    comparison = compare_protein_inference_strategies(
        scenario.records,
        picked_threshold=picked_threshold,
    )
    expected_present = set(scenario.expected_present_proteins)
    expected_absent = set(scenario.expected_absent_proteins)
    fasta_protein_refs = set(scenario.fasta_protein_refs)
    method_assessments: list[ProteinInferenceMethodAssessment] = []
    disagreement_count = 0
    for selection in comparison.selections:
        selected = set(selection.selected_proteins)
        true_positives = selected & expected_present
        false_positives = selected & expected_absent
        false_negatives = expected_present - selected
        selected_missing_fasta = (
            selected - fasta_protein_refs if fasta_protein_refs else set()
        )
        precision_denominator = len(true_positives) + len(false_positives)
        recall_denominator = len(true_positives) + len(false_negatives)
        precision = (
            len(true_positives) / precision_denominator
            if precision_denominator
            else 0.0
        )
        recall = len(true_positives) / recall_denominator if recall_denominator else 0.0
        precision_low, precision_high = _wilson_interval(
            len(true_positives),
            precision_denominator,
        )
        recall_low, recall_high = _wilson_interval(
            len(true_positives),
            recall_denominator,
        )
        trustworthy = (
            precision_low >= 0.5 and not false_positives and not selected_missing_fasta
        )
        note = (
            "strategy keeps the expected proteins without absent-protein bleed"
            if trustworthy
            else (
                "strategy still promotes proteins missing from the FASTA catalog"
                if selected_missing_fasta
                else "strategy still shows absent-protein bleed or an unstable lower-bound interval"
            )
        )
        if false_positives or false_negatives or selected_missing_fasta:
            disagreement_count += 1
        method_assessments.append(
            ProteinInferenceMethodAssessment(
                strategy_kind=selection.strategy_kind,
                strategy_label=selection.strategy_label,
                selected_proteins=selection.selected_proteins,
                true_positive_count=len(true_positives),
                false_positive_count=len(false_positives),
                false_negative_count=len(false_negatives),
                precision=precision,
                precision_interval_low=precision_low,
                precision_interval_high=precision_high,
                recall=recall,
                recall_interval_low=recall_low,
                recall_interval_high=recall_high,
                false_positive_proteins=tuple(sorted(false_positives)),
                missed_proteins=tuple(sorted(false_negatives)),
                selected_missing_fasta_proteins=tuple(sorted(selected_missing_fasta)),
                trustworthy_for_review=trustworthy,
                trust_note=note,
            )
        )
    ambiguity_exposed = scenario.ambiguity_should_be_visible and (
        disagreement_count > 0
        or any(
            assessment.selected_missing_fasta_proteins
            for assessment in method_assessments
        )
    )
    return ProteinInferenceBenchmarkReport(
        scenario_id=scenario.scenario_id,
        scenario_kind=scenario.scenario_kind,
        expected_present_proteins=tuple(sorted(expected_present)),
        expected_absent_proteins=tuple(sorted(expected_absent)),
        fasta_protein_refs=tuple(sorted(fasta_protein_refs)),
        shared_peptide_pressure=any(
            len(record.protein_refs) > 1 for record in scenario.records
        ),
        isoform_pressure=any(
            len({_base_accession(ref) for ref in record.protein_refs}) == 1
            and len(record.protein_refs) > 1
            for record in scenario.records
        ),
        homolog_family_pressure=(
            scenario.scenario_kind
            is ProteinInferenceBenchmarkScenarioKind.HOMOLOG_FAMILY_HEAVY
        ),
        contaminant_pressure=any(
            protein_ref.startswith("CON__")
            for record in scenario.records
            for protein_ref in record.protein_refs
        ),
        all_decoy_pressure=all(
            record.target_decoy_label is TargetDecoyLabel.DECOY
            for record in scenario.records
        ),
        all_target_pressure=all(
            record.target_decoy_label is TargetDecoyLabel.TARGET
            for record in scenario.records
        ),
        tied_score_pressure=_has_tied_top_score(scenario.records),
        missing_fasta_pressure=bool(fasta_protein_refs)
        and any(
            protein_ref not in fasta_protein_refs
            for record in scenario.records
            for protein_ref in record.protein_refs
        ),
        ambiguity_should_be_visible=scenario.ambiguity_should_be_visible,
        ambiguity_exposed=ambiguity_exposed,
        method_assessments=tuple(method_assessments),
        disagreement_count=disagreement_count,
        scenario_note=scenario.note,
    )


def build_protein_inference_benchmark_suite(
    scenarios: tuple[ProteinInferenceBenchmarkScenario, ...],
    *,
    picked_threshold: float = 0.05,
) -> ProteinInferenceBenchmarkSuiteReport:
    """Aggregate multiple protein-inference pressure scenarios into one suite."""

    reports = tuple(
        build_protein_inference_benchmark_report(
            scenario,
            picked_threshold=picked_threshold,
        )
        for scenario in scenarios
    )
    lower_bounds = [
        assessment.precision_interval_low
        for report in reports
        for assessment in report.method_assessments
    ]
    recall_lower_bounds = [
        assessment.recall_interval_low
        for report in reports
        for assessment in report.method_assessments
    ]
    covered_strategy_kinds = tuple(
        sorted(
            {
                assessment.strategy_kind
                for report in reports
                for assessment in report.method_assessments
            },
            key=lambda kind: kind.value,
        )
    )
    return ProteinInferenceBenchmarkSuiteReport(
        reports=reports,
        covered_strategy_kinds=covered_strategy_kinds,
        scenario_ids=tuple(report.scenario_id for report in reports),
        scenario_kinds=tuple(report.scenario_kind for report in reports),
        shared_peptide_scenario_count=sum(
            report.scenario_kind
            is ProteinInferenceBenchmarkScenarioKind.SHARED_PEPTIDE_HEAVY
            for report in reports
        ),
        isoform_scenario_count=sum(
            report.scenario_kind is ProteinInferenceBenchmarkScenarioKind.ISOFORM_HEAVY
            for report in reports
        ),
        homolog_family_scenario_count=sum(
            report.scenario_kind
            is ProteinInferenceBenchmarkScenarioKind.HOMOLOG_FAMILY_HEAVY
            for report in reports
        ),
        contaminant_scenario_count=sum(
            report.scenario_kind
            is ProteinInferenceBenchmarkScenarioKind.CONTAMINANT_HEAVY
            for report in reports
        ),
        all_decoy_scenario_count=sum(
            report.scenario_kind is ProteinInferenceBenchmarkScenarioKind.ALL_DECOY
            for report in reports
        ),
        all_target_scenario_count=sum(
            report.scenario_kind is ProteinInferenceBenchmarkScenarioKind.ALL_TARGET
            for report in reports
        ),
        tied_score_scenario_count=sum(
            report.scenario_kind is ProteinInferenceBenchmarkScenarioKind.TIED_SCORE
            for report in reports
        ),
        missing_fasta_scenario_count=sum(
            report.scenario_kind
            is ProteinInferenceBenchmarkScenarioKind.MISSING_FASTA_ENTRY
            for report in reports
        ),
        ambiguity_visible_scenario_count=sum(
            report.ambiguity_should_be_visible and report.ambiguity_exposed
            for report in reports
        ),
        hidden_ambiguity_scenario_count=sum(
            report.ambiguity_should_be_visible and not report.ambiguity_exposed
            for report in reports
        ),
        worst_precision_lower_bound=min(lower_bounds) if lower_bounds else 0.0,
        worst_recall_lower_bound=min(recall_lower_bounds)
        if recall_lower_bounds
        else 0.0,
        scenario_count=len(reports),
        note=(
            "protein-inference benchmark suite keeps shared-peptide, isoform, homolog-family, contaminant, all-target, all-decoy, tied-score, and missing-fasta pressure explicit across named truth scenarios"
            if reports
            else "protein-inference benchmark suite has no scenarios to evaluate"
        ),
    )


def build_core_protein_inference_benchmark_suite(
    *,
    picked_threshold: float = 0.05,
) -> ProteinInferenceBenchmarkSuiteReport:
    """Build the owned benchmark suite over the full protein-inference catalog."""

    return build_protein_inference_benchmark_suite(
        build_core_protein_inference_benchmark_scenarios(),
        picked_threshold=picked_threshold,
    )


def render_protein_inference_benchmark_summary_tsv(
    suite: ProteinInferenceBenchmarkSuiteReport,
) -> str:
    """Render one compact suite summary ledger as TSV."""

    rows = (
        ("scenario_count", suite.scenario_count),
        ("shared_peptide_scenario_count", suite.shared_peptide_scenario_count),
        ("isoform_scenario_count", suite.isoform_scenario_count),
        ("homolog_family_scenario_count", suite.homolog_family_scenario_count),
        ("contaminant_scenario_count", suite.contaminant_scenario_count),
        ("all_decoy_scenario_count", suite.all_decoy_scenario_count),
        ("all_target_scenario_count", suite.all_target_scenario_count),
        ("tied_score_scenario_count", suite.tied_score_scenario_count),
        ("missing_fasta_scenario_count", suite.missing_fasta_scenario_count),
        ("ambiguity_visible_scenario_count", suite.ambiguity_visible_scenario_count),
        ("hidden_ambiguity_scenario_count", suite.hidden_ambiguity_scenario_count),
        ("worst_precision_lower_bound", suite.worst_precision_lower_bound),
        ("worst_recall_lower_bound", suite.worst_recall_lower_bound),
        (
            "covered_strategy_kinds",
            ";".join(kind.value for kind in suite.covered_strategy_kinds),
        ),
        ("scenario_ids", ";".join(suite.scenario_ids)),
        ("note", suite.note),
    )
    return (
        "field\tvalue\n"
        + "\n".join(f"{field}\t{value}" for field, value in rows)
        + "\n"
    )


def render_protein_inference_benchmark_scenarios_tsv(
    suite: ProteinInferenceBenchmarkSuiteReport,
) -> str:
    """Render the named benchmark scenarios as TSV."""

    lines = [
        "\t".join(
            (
                "scenario_id",
                "scenario_kind",
                "expected_present_proteins",
                "expected_absent_proteins",
                "fasta_protein_refs",
                "shared_peptide_pressure",
                "isoform_pressure",
                "homolog_family_pressure",
                "contaminant_pressure",
                "all_decoy_pressure",
                "all_target_pressure",
                "tied_score_pressure",
                "missing_fasta_pressure",
                "ambiguity_should_be_visible",
                "ambiguity_exposed",
                "disagreement_count",
                "scenario_note",
            )
        )
    ]
    for report in suite.reports:
        lines.append(
            "\t".join(
                (
                    report.scenario_id,
                    report.scenario_kind.value,
                    ";".join(report.expected_present_proteins),
                    ";".join(report.expected_absent_proteins),
                    ";".join(report.fasta_protein_refs),
                    str(report.shared_peptide_pressure).lower(),
                    str(report.isoform_pressure).lower(),
                    str(report.homolog_family_pressure).lower(),
                    str(report.contaminant_pressure).lower(),
                    str(report.all_decoy_pressure).lower(),
                    str(report.all_target_pressure).lower(),
                    str(report.tied_score_pressure).lower(),
                    str(report.missing_fasta_pressure).lower(),
                    str(report.ambiguity_should_be_visible).lower(),
                    str(report.ambiguity_exposed).lower(),
                    str(report.disagreement_count),
                    report.scenario_note,
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_protein_inference_benchmark_assessments_tsv(
    suite: ProteinInferenceBenchmarkSuiteReport,
) -> str:
    """Render one method-assessment ledger across all benchmark scenarios."""

    lines = [
        "\t".join(
            (
                "scenario_id",
                "scenario_kind",
                "strategy_kind",
                "strategy_label",
                "selected_proteins",
                "true_positive_count",
                "false_positive_count",
                "false_negative_count",
                "precision",
                "precision_interval_low",
                "precision_interval_high",
                "recall",
                "recall_interval_low",
                "recall_interval_high",
                "false_positive_proteins",
                "missed_proteins",
                "selected_missing_fasta_proteins",
                "trustworthy_for_review",
                "trust_note",
            )
        )
    ]
    for report in suite.reports:
        for assessment in report.method_assessments:
            lines.append(
                "\t".join(
                    (
                        report.scenario_id,
                        report.scenario_kind.value,
                        assessment.strategy_kind.value,
                        assessment.strategy_label,
                        ";".join(assessment.selected_proteins),
                        str(assessment.true_positive_count),
                        str(assessment.false_positive_count),
                        str(assessment.false_negative_count),
                        f"{assessment.precision:.6g}",
                        f"{assessment.precision_interval_low:.6g}",
                        f"{assessment.precision_interval_high:.6g}",
                        f"{assessment.recall:.6g}",
                        f"{assessment.recall_interval_low:.6g}",
                        f"{assessment.recall_interval_high:.6g}",
                        ";".join(assessment.false_positive_proteins),
                        ";".join(assessment.missed_proteins),
                        ";".join(assessment.selected_missing_fasta_proteins),
                        str(assessment.trustworthy_for_review).lower(),
                        assessment.trust_note,
                    )
                )
            )
    return "\n".join(lines) + "\n"


def build_picked_group_fdr_benchmark_plan() -> PickedGroupFdrBenchmarkPlan:
    """Declare the minimum benchmark program required before picked-group claims travel."""

    return PickedGroupFdrBenchmarkPlan(
        claim_ready=False,
        current_state=(
            "picked protein competition exists, but picked-group FDR remains unclaimed "
            "until grouped competition is benchmarked under real pressure families"
        ),
        required_scenarios=(
            PickedGroupFdrBenchmarkScenarioPlan(
                scenario_id="picked-group-decoy-pairs",
                pressure=PickedGroupBenchmarkPressure.DECOY_PAIRED_GROUPS,
                scientific_question=(
                    "Do grouped target and decoy families pair deterministically when a shared evidence set spans multiple protein groups?"
                ),
                blocked_claim="picked-group FDR support",
            ),
            PickedGroupFdrBenchmarkScenarioPlan(
                scenario_id="picked-group-shared-peptides",
                pressure=PickedGroupBenchmarkPressure.SHARED_PEPTIDE_GROUPS,
                scientific_question=(
                    "Does grouped competition avoid promoting absent proteins that borrow only shared-peptide support?"
                ),
                blocked_claim="shared-peptide-safe picked-group inference",
            ),
            PickedGroupFdrBenchmarkScenarioPlan(
                scenario_id="picked-group-isoform-collisions",
                pressure=PickedGroupBenchmarkPressure.ISOFORM_COLLISIONS,
                scientific_question=(
                    "Do isoform-family collisions stay explicit instead of collapsing into one overstated group winner?"
                ),
                blocked_claim="isoform-safe picked-group inference",
            ),
            PickedGroupFdrBenchmarkScenarioPlan(
                scenario_id="picked-group-contaminants",
                pressure=PickedGroupBenchmarkPressure.CONTAMINANT_GROUP_PRESSURE,
                scientific_question=(
                    "Can contaminant-heavy groups be rejected without suppressing biologically supported target groups?"
                ),
                blocked_claim="contaminant-aware picked-group promotion",
            ),
        ),
        blocked_by=(
            "group-level target-decoy competition is not benchmarked yet",
            "no truth-scored group fixtures currently cover isoform and contaminant pressure together",
            "workflow claims would outrun evidence if picked-group support were promoted today",
        ),
        next_artifacts=(
            "grouped_truth_fixture_manifest.json",
            "picked_group_benchmark_report.json",
            "picked_group_disagreement_dossier.json",
        ),
    )


def build_identification_workflow_claim_review(
    *,
    workflow_id: str,
    benchmark_suite: ProteinInferenceBenchmarkSuiteReport,
    material_loss_count: int = 0,
    engine_disagreement_count: int = 0,
    contaminant_risk: bool = False,
    calibration_release_blocked: bool = False,
) -> IdentificationWorkflowClaimReview:
    """Require a workflow claim to pass a scientific trust rubric before promotion."""

    scenario_kinds = set(benchmark_suite.scenario_kinds)
    criteria = (
        WorkflowTrustCriterionResult(
            criterion_id="shared-peptide-pressure-covered",
            passed=ProteinInferenceBenchmarkScenarioKind.SHARED_PEPTIDE_HEAVY
            in scenario_kinds,
            detail="shared-peptide-heavy truth pressure is present in the benchmark suite",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="isoform-pressure-covered",
            passed=ProteinInferenceBenchmarkScenarioKind.ISOFORM_HEAVY
            in scenario_kinds,
            detail="isoform-heavy truth pressure is present in the benchmark suite",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="homolog-family-pressure-covered",
            passed=ProteinInferenceBenchmarkScenarioKind.HOMOLOG_FAMILY_HEAVY
            in scenario_kinds,
            detail="homolog-family truth pressure is present in the benchmark suite",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="contaminant-pressure-covered",
            passed=ProteinInferenceBenchmarkScenarioKind.CONTAMINANT_HEAVY
            in scenario_kinds,
            detail="contaminant-heavy truth pressure is present in the benchmark suite",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="decoy-pressure-covered",
            passed=ProteinInferenceBenchmarkScenarioKind.ALL_DECOY in scenario_kinds,
            detail="all-decoy truth pressure is present in the benchmark suite",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="all-target-pressure-covered",
            passed=ProteinInferenceBenchmarkScenarioKind.ALL_TARGET in scenario_kinds,
            detail="all-target truth pressure is present in the benchmark suite",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="tied-score-pressure-covered",
            passed=ProteinInferenceBenchmarkScenarioKind.TIED_SCORE in scenario_kinds,
            detail="tied-score ambiguity pressure is present in the benchmark suite",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="missing-fasta-pressure-covered",
            passed=ProteinInferenceBenchmarkScenarioKind.MISSING_FASTA_ENTRY
            in scenario_kinds,
            detail="missing-fasta truth pressure is present in the benchmark suite",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="hidden-ambiguity-absent",
            passed=benchmark_suite.hidden_ambiguity_scenario_count == 0,
            detail=(
                "hidden ambiguity scenario count is "
                f"{benchmark_suite.hidden_ambiguity_scenario_count}"
            ),
        ),
        WorkflowTrustCriterionResult(
            criterion_id="precision-lower-bound-supported",
            passed=benchmark_suite.worst_precision_lower_bound >= 0.5,
            detail=(
                "worst strategy precision lower bound is "
                f"{benchmark_suite.worst_precision_lower_bound:.2f}"
            ),
        ),
        WorkflowTrustCriterionResult(
            criterion_id="recall-lower-bound-supported",
            passed=benchmark_suite.worst_recall_lower_bound >= 0.3,
            detail=(
                "worst strategy recall lower bound is "
                f"{benchmark_suite.worst_recall_lower_bound:.2f}"
            ),
        ),
        WorkflowTrustCriterionResult(
            criterion_id="material-adapter-loss-absent",
            passed=material_loss_count == 0,
            detail=f"material adapter-loss count is {material_loss_count}",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="engine-disagreement-contained",
            passed=engine_disagreement_count == 0,
            detail=f"material engine-disagreement count is {engine_disagreement_count}",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="contaminant-risk-contained",
            passed=not contaminant_risk,
            detail="contaminant-driven protein promotion is not unresolved",
        ),
        WorkflowTrustCriterionResult(
            criterion_id="calibration-not-release-blocked",
            passed=not calibration_release_blocked,
            detail="calibration release gate is not blocked",
        ),
    )
    refusal_reasons = tuple(
        criterion.criterion_id for criterion in criteria if not criterion.passed
    )
    passed_count = sum(1 for criterion in criteria if criterion.passed)
    return IdentificationWorkflowClaimReview(
        workflow_id=workflow_id,
        accepted=not refusal_reasons,
        trust_score=passed_count / len(criteria),
        precision_floor=benchmark_suite.worst_precision_lower_bound,
        recall_floor=benchmark_suite.worst_recall_lower_bound,
        criteria=criteria,
        refusal_reasons=refusal_reasons,
    )
