# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from typing import Any, cast

from bijux_proteomics import SuccessCriterion, create_program_spec, parse_chromatogram_qc_table
from bijux_proteomics.programs import MeasurementDirection
from bijux_proteomics_intelligence import CandidateAssessment, build_follow_up_candidate_path
from bijux_proteomics_knowledge import EvidenceBundle, EvidenceRecord
from bijux_proteomics_knowledge.references import (
    KnowledgeWorkflowFamily,
    get_benchmark_manifest,
)
from bijux_proteomics_lab import (
    AssayOutcome,
    AssayResultState,
    ExecutableAssayPlan,
    ExperimentOutcome,
    InstrumentMethodMetadata,
    OperationalFollowUpPath,
    ProtocolControlRequirement,
    ProtocolFailureCaveat,
    ReviewPacket,
    SamplePreparationMetadata,
    TargetedBenchmarkClaimSupport,
    TargetedBenchmarkReport,
    TargetedOperatorRunReport,
    TargetedTransitionReview,
    build_handoff_explanation,
    build_lims_export_bundle,
    build_operational_follow_up_path,
    build_protocol_attachment,
    build_targeted_benchmark_report,
    build_targeted_operator_run_report,
)
from bijux_proteomics_lab.lifecycle import CandidateHandoffValidation


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _review_scenario_fixture(name: str) -> dict[str, Any]:
    path = (
        Path(__file__).resolve().parents[2]
        / "bijux-proteomics-intelligence"
        / "tests"
        / "fixtures"
        / "review_scenarios"
        / f"{name}.json"
    )
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _handoff_fixture(name: str) -> dict[str, Any]:
    path = Path(__file__).parent / "fixtures" / "handoffs" / name
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _program_from_fixture(payload: dict[str, Any]) -> object:
    program_data = cast(dict[str, Any], payload["program"])
    criterion_data = cast(dict[str, Any], payload["criterion"])
    program = create_program_spec(
        program_id=str(program_data["program_id"]),
        name=str(program_data["name"]),
        objective=str(program_data["objective"]),
        target_id=str(program_data["target_id"]),
        target_name=str(program_data["target_name"]),
        sequence=str(program_data["sequence"]),
        organism=str(program_data["organism"]),
        mechanism=str(program_data["mechanism"]),
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id=str(criterion_data["criterion_id"]),
            metric=str(criterion_data["metric"]),
            direction=MeasurementDirection.MAXIMIZE,
            threshold=float(criterion_data["threshold"]),
        )
    )
    return program


def _assessments_from_fixture(payload: dict[str, Any]) -> tuple[CandidateAssessment, ...]:
    candidates = cast(list[dict[str, Any]], payload["candidates"])
    return tuple(CandidateAssessment.model_validate(item) for item in candidates)


def _bundle_from_fixture(payload: dict[str, Any]) -> EvidenceBundle:
    records_payload = cast(list[dict[str, Any]], payload["evidence_records"])
    program_data = cast(dict[str, Any], payload["program"])
    now = datetime.now(UTC)
    records: list[EvidenceRecord] = []
    for item in records_payload:
        record_payload = dict(item)
        observed_days_ago = int(record_payload.pop("observed_days_ago", 0))
        record_payload["observed_at"] = now - timedelta(days=observed_days_ago)
        records.append(EvidenceRecord.model_validate(record_payload))
    return EvidenceBundle(
        bundle_id=f"{program_data['program_id']}-bundle",
        target_id=str(program_data["target_id"]),
        records=records,
    )


def _protocol_attachment():
    return build_protocol_attachment(
        sample_preparation=SamplePreparationMetadata(
            protocol_id="prep-targeted-benchmark",
            digestion_protocol="trypsin overnight",
            cleanup_method="solid-phase extraction",
        ),
        instrument_method=InstrumentMethodMetadata(
            method_id="prm-benchmark-method",
            instrument="orbitrap",
            acquisition_mode="PRM",
            gradient_minutes=60.0,
            ms1_resolution=60000,
            ms2_resolution=30000,
            collision_energy=28.0,
        ),
        protocol_version="3.0",
        required_controls=(
            ProtocolControlRequirement(
                control_id="pooled-reference",
                summary="shared pooled reference",
                failure_if_missing="transition timing cannot be normalized safely",
            ),
        ),
        failure_caveats=(
            ProtocolFailureCaveat(
                caveat_id="carryover-watch",
                triggering_condition="high-abundance precursor precedes low-abundance sample",
                operational_effect="transition ratios may be inflated by carryover",
                mitigation="insert wash and bridge controls",
            ),
        ),
    )


def _supported_operational_path() -> tuple[
    CandidateHandoffValidation,
    TargetedTransitionReview,
    ReviewPacket,
    ExecutableAssayPlan,
    OperationalFollowUpPath,
]:
    fixture = _handoff_fixture("supported_targeted_follow_up.json")
    handoff_validation = CandidateHandoffValidation.model_validate(
        fixture["handoff_validation"]
    )
    transition_review = TargetedTransitionReview.model_validate(
        fixture["transition_review"]
    ).model_copy(
        update={
            "approved_transition_ids": ("tr-egfr-1", "tr-egfr-2"),
            "exploratory_transition_ids": (),
            "notes": ("targeted transition panel is fully ready for benchmark handoff",),
        }
    )
    review_packet = ReviewPacket.model_validate(fixture["review_packet"])
    executable_plan = ExecutableAssayPlan.model_validate(fixture["executable_plan"])
    outcome = ExperimentOutcome.model_validate(fixture["outcome"]).model_copy(
        update={
            "assay_outcomes": [
                AssayOutcome(
                    assay_id="prm-assay",
                    passed=True,
                    result_state=AssayResultState.PASSED,
                    observation_summary="PRM transition cluster reproduced the prioritized phosphosite signal",
                    replicate_count=3,
                    uncertainty=0.08,
                ),
                AssayOutcome(
                    assay_id="orthogonal-assay",
                    passed=True,
                    result_state=AssayResultState.PASSED,
                    observation_summary="orthogonal immunoblot agreed with the targeted direction",
                    replicate_count=2,
                    uncertainty=0.12,
                ),
            ]
        }
    )
    path = build_operational_follow_up_path(
        candidate_id=cast(str, fixture["candidate_id"]),
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
        outcome=outcome,
        target_id=cast(str, fixture["target_id"]),
        claim_links=cast(dict[str, list[str]], fixture["claim_links"]),
    )
    return handoff_validation, transition_review, review_packet, executable_plan, path


def test_build_targeted_benchmark_report_connects_discovery_evidence_to_lab_outputs() -> (
    None
):
    scenario = _review_scenario_fixture("targeted_assay_review")
    program = _program_from_fixture(scenario)
    assessments = _assessments_from_fixture(scenario)
    base_bundle = _bundle_from_fixture(scenario)
    bundle = base_bundle.model_copy(
        update={
            "records": [
                *base_bundle.records,
                EvidenceRecord.model_validate(
                    {
                        "evidence_id": "targeted-support-3",
                        "kind": "literature",
                        "title": "targeted literature support",
                        "source": "PMID:targeted-benchmark",
                        "source_type": "literature",
                        "claim": "published targeted assay literature supports the same transition family",
                        "confidence": 0.84,
                        "strength": "supporting",
                        "decision_tags": ["progression"],
                        "observed_at": datetime.now(UTC) - timedelta(days=10),
                    }
                ),
                EvidenceRecord.model_validate(
                    {
                        "evidence_id": "targeted-support-4",
                        "kind": "structure",
                        "title": "targeted structural support",
                        "source": "structure-model-1",
                        "source_type": "structure_model",
                        "claim": "structural context preserves the prioritized engagement hypothesis",
                        "confidence": 0.8,
                        "strength": "supporting",
                        "decision_tags": ["progression"],
                        "observed_at": datetime.now(UTC) - timedelta(days=8),
                    }
                ),
            ]
        }
    )
    follow_up_path = build_follow_up_candidate_path(
        program,
        list(assessments),
        bundle,
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
    )
    handoff_validation, transition_review, review_packet, executable_plan, operational_path = (
        _supported_operational_path()
    )
    explanation = build_handoff_explanation(
        candidate_id=handoff_validation.candidate_id,
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
    )
    lims_bundle = build_lims_export_bundle(
        bundle_id="lims-targeted-benchmark",
        system_name="benchling-lims",
        candidate_id=handoff_validation.candidate_id,
        execution_request=operational_path.execution_request,
        protocol_attachment=_protocol_attachment(),
        explanation=explanation,
    )
    chromatogram_report = parse_chromatogram_qc_table(
        _repo_root()
        / "packages"
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "formats"
        / "targeted_benchmark_qc.tsv"
    )
    manifest = get_benchmark_manifest("benchmark:targeted_transition_quality_control")

    report = build_targeted_benchmark_report(
        benchmark_manifest=manifest,
        candidate_assessments=assessments,
        follow_up_path=follow_up_path,
        chromatogram_report=chromatogram_report,
        transition_review=transition_review,
        lims_export_bundle=lims_bundle,
        operational_path=operational_path,
        cache_age_days=7,
    )
    operator_run = build_targeted_operator_run_report(report)

    assert isinstance(report, TargetedBenchmarkReport)
    assert report.recommended_candidate_id == "targeted-heavy-peptide-a"
    assert report.overall_support is TargetedBenchmarkClaimSupport.STRONG_SUPPORT
    assert all(
        summary.support is TargetedBenchmarkClaimSupport.STRONG_SUPPORT
        for summary in report.claim_summaries
    )
    assert report.lims_export_bundle.bundle_id == "lims-targeted-benchmark"
    assert report.operational_path.execution_request.ready_for_lab_review is True
    assert isinstance(operator_run, TargetedOperatorRunReport)
    assert operator_run.ready_for_operator_review is True
    assert "lims-targeted-benchmark" in operator_run.artifact_ids
