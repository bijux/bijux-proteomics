# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.program_spec import (
    EvidenceNeed,
    create_program_spec,
)
from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    build_review_ready_evidence_bundle,
    filter_psms_by_fdr,
    parse_psm_tsv,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import (
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.review import (
    build_ptm_lab_validation_packet,
    build_ptm_occupancy_counterpart_report,
)
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantRollupMethod,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.review import build_quant_review_bundle
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics_intelligence.candidates.lifecycle import CandidateRiskProfile
from bijux_proteomics_intelligence.candidates.ranking import (
    CandidateRanking,
    RankedCandidate,
)
from bijux_proteomics_intelligence.judgment.scenarios import (
    EvaluatorPolicyBundle,
    evaluate_all_scenarios,
)
from bijux_proteomics_intelligence.reviews.decision_briefs import (
    build_intelligence_review_packet,
)
from bijux_proteomics_knowledge.memory.models.claims import ClaimStatus, build_claim
from bijux_proteomics_knowledge.memory.models.evidence import (
    DecisionReadiness,
    EvidenceBundle,
    EvidenceCoverage,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.reviews.decision_briefs import (
    build_knowledge_decision_brief,
)
from bijux_proteomics_lab.handoffs import TargetedTransitionReview
from bijux_proteomics_lab.lifecycle import CandidateHandoffValidation
from bijux_proteomics_lab.outcomes import ExperimentOutcome
from bijux_proteomics_lab.planning import (
    ExecutableAssayPlan,
    ReviewPacket,
    build_lab_review_packet_bundle,
)
from bijux_proteomics_lab.reconciliation import build_operational_follow_up_path
from bijux_proteomics_runtime.workflows import (
    WorkflowFailureCategory,
    WorkflowPacketSerializationMode,
    WorkflowStageAcceptance,
    build_flagship_workflow_acceptance_dossier,
    build_flagship_workflow_failure_taxonomy,
    build_flagship_workflow_handoff_contracts,
    build_minimum_real_workflow_proof_bar,
    build_workflow_stage_packet_boundary_contracts,
)
from bijux_proteomics_runtime.workflows.plans import (
    build_proteomics_workflow_manifest,
    build_workflow_manifest_explanation_report,
)


def _runtime_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "production_run" / name


def _core_fixture(*parts: str) -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "packages"
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / Path(*parts)
    )


def _lab_fixture(name: str) -> dict[str, Any]:
    path = (
        Path(__file__).resolve().parents[4]
        / "packages"
        / "bijux-proteomics-lab"
        / "tests"
        / "fixtures"
        / "handoffs"
        / name
    )
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _default_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def _ready_state() -> DecisionReadiness:
    return DecisionReadiness(
        target_id="target-packet",
        ready=True,
        blockers=[],
        recommendations=[],
        coverage=EvidenceCoverage(
            bundle_id="bundle-1",
            target_id="target-packet",
            by_kind={
                "literature": 1,
                "structure": 1,
                "assay": 2,
                "pathway": 0,
                "safety": 0,
            },
            missing_kinds=[],
            decisive_records=2,
            mean_confidence=0.85,
        ),
    )


def _quant_records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="qb-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=950.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-003",
            sample_id="s3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=120.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-004",
            sample_id="s4",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _quant_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="s2.mzml",
            batch="b2",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s4",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="s4.mzml",
            batch="b2",
        ),
    )


def test_flagship_workflow_acceptance_dossier_distinguishes_real_proof_axes() -> None:
    dossier = build_flagship_workflow_acceptance_dossier()

    assert dossier.workflow_family == "flagship-workflows"
    stage_ids = {stage.stage_id for stage in dossier.stages}
    assert stage_ids == {
        contract.stage_id for contract in build_flagship_workflow_handoff_contracts()
    }
    manifest_stage = next(
        stage
        for stage in dossier.stages
        if stage.stage_id == "runtime-workflow-manifest"
    )
    assert isinstance(manifest_stage, WorkflowStageAcceptance)
    assert manifest_stage.typed_only is True
    assert manifest_stage.executable is False
    assert manifest_stage.replayable is False

    downstream_stage = next(
        stage
        for stage in dossier.stages
        if stage.stage_id == "lab-operational-follow-up"
    )
    assert downstream_stage.executable is True
    assert downstream_stage.replayable is True
    assert downstream_stage.benchmarked is True
    assert downstream_stage.lab_reviewed is True


def test_flagship_workflow_failure_taxonomy_separates_scientific_and_engineering_breakage() -> (
    None
):
    taxonomy = build_flagship_workflow_failure_taxonomy()

    assert taxonomy.workflow_family == "flagship-workflows"
    categories = {entry.category for entry in taxonomy.entries}
    assert WorkflowFailureCategory.ENGINEERING_BREAKAGE in categories
    assert WorkflowFailureCategory.SCIENTIFIC_INCOMPLETENESS in categories
    assert WorkflowFailureCategory.REVIEW_AUTHORITY_BOUNDARY in categories
    assert WorkflowFailureCategory.OPERATIONAL_EXECUTION_CONFLICT in categories
    assert WorkflowFailureCategory.EXTERNAL_CAPABILITY_GAP in categories


def test_minimum_real_workflow_proof_bar_requires_reproducibility_reviews_limits_and_benchmarks() -> (
    None
):
    proof_bar = build_minimum_real_workflow_proof_bar()

    requirement_ids = {
        requirement.requirement_id for requirement in proof_bar.requirements
    }
    assert requirement_ids == {
        "reproducible-run",
        "reviewed-artifacts",
        "known-limits",
        "serious-benchmark-corpus",
    }
    for requirement in proof_bar.requirements:
        assert requirement.validating_surface_refs
        assert requirement.validating_test_paths


def test_stage_review_packets_survive_package_boundaries_as_serializable_outputs() -> (
    None
):
    manifest = build_proteomics_workflow_manifest(
        proteins_path=_runtime_fixture("proteins.fasta"),
        spectra_path=_runtime_fixture("spectra.mgf"),
        identifications_path=_runtime_fixture("results.tsv"),
        features_path=_runtime_fixture("ms1_features.tsv"),
        design_path=_runtime_fixture("design.tsv"),
        sample_id="sample-A",
    )
    manifest_packet = build_workflow_manifest_explanation_report(manifest)

    identification_report = parse_psm_tsv(
        _core_fixture("psm", "protein_inference_results.tsv"),
        mapping=_default_mapping(),
    )
    accepted = filter_psms_by_fdr(
        identification_report.accepted_records, threshold=0.05
    )
    identification_packet = build_review_ready_evidence_bundle(
        accepted,
        threshold=0.05,
        score_orientation="higher_better",
        ptm_site_keys_by_peptide={"SHAREDK": ("P11111:S5:Phospho",)},
        quant_support_by_protein={"P11111": {"C1": 2200.0}},
    )

    quant_packet = build_quant_review_bundle(
        _quant_records(),
        design_entries=_quant_design(),
        normalization_method=NormalizationMethod.MEDIAN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    parsed = parse_ptm_localization_tsv(
        _core_fixture("ptm", "localization_results.tsv")
    )
    fasta = parse_fasta_document(
        _core_fixture("fasta", "ptm_sites.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    protein_sequences = {
        record.canonical_accession: record.residues for record in fasta.accepted_records
    }
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=protein_sequences,
    )
    sites = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(
        _core_fixture("ptm", "ptm_features.tsv")
    ).accepted_records
    occupancy = build_ptm_occupancy_counterpart_report(sites, feature_records=features)
    ptm_packet = build_ptm_lab_validation_packet(sites, occupancy_report=occupancy)

    knowledge_bundle = EvidenceBundle(
        bundle_id="bundle-review",
        target_id="target-review",
        records=[
            EvidenceRecord(
                evidence_id="review-1",
                kind=EvidenceKind.ASSAY,
                title="assay",
                source="lab",
                claim="supports progression",
                decision_tags=["progression"],
                confidence=0.88,
                strength=EvidenceStrength.DECISIVE,
            )
        ],
    )
    knowledge_claims = [
        build_claim(
            claim_id="claim-review-1",
            target_id="target-review",
            statement="Candidate can progress.",
            evidence_ids=["review-1"],
            status=ClaimStatus.SUPPORTED,
            resolution_assays=["orthogonal assay"],
        )
    ]
    knowledge_packet = build_knowledge_decision_brief(
        knowledge_bundle,
        knowledge_claims,
        decision_tag="progression",
        workflow_family=KnowledgeWorkflowFamily.DDA,
        required_modalities=[EvidenceKind.ASSAY.value],
    )

    program = create_program_spec(
        program_id="prog-packet",
        name="decision brief",
        objective="compose intelligence decision brief",
        target_id="target-packet",
        target_name="Target Packet",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="integrate intelligence outputs for review",
    )
    ranking = CandidateRanking(
        program_id="prog-packet",
        ranked_candidates=[
            RankedCandidate(candidate_id="candidate-1", score=1.2, rank=1)
        ],
    )
    risks = [
        CandidateRiskProfile(
            candidate_id="candidate-1", residual_risk=0.6, safety_risk=0.6
        )
    ]
    grouped = evaluate_all_scenarios(
        program,
        ranking,
        _ready_state(),
        risks,
        policies=EvaluatorPolicyBundle(),
    )
    intelligence_packet = build_intelligence_review_packet(grouped, ranking, risks)

    lab_program = create_program_spec(
        program_id="prog-review-bundle",
        name="review bundle",
        objective="bundle review rationale and unresolved risks",
        target_id="target-review",
        target_name="Target Review",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a productive conformation",
    )
    lab_program.evidence_needs = [EvidenceNeed.LITERATURE, EvidenceNeed.STRUCTURE]
    lab_program.assay_panel.append(
        AssayRequirement(
            assay_id="gate-binding",
            purpose="confirm target engagement",
            readout="binding_score",
            sample_kind="biophysical",
            blocking=True,
        )
    )
    lab_packet = build_lab_review_packet_bundle(lab_program, knowledge_bundle, [])

    follow_up_fixture = _lab_fixture("supported_targeted_follow_up.json")
    follow_up_packet = build_operational_follow_up_path(
        candidate_id=cast(str, follow_up_fixture["candidate_id"]),
        handoff_validation=CandidateHandoffValidation.model_validate(
            follow_up_fixture["handoff_validation"]
        ),
        transition_review=TargetedTransitionReview.model_validate(
            follow_up_fixture["transition_review"]
        ),
        review_packet=ReviewPacket.model_validate(follow_up_fixture["review_packet"]),
        executable_plan=ExecutableAssayPlan.model_validate(
            follow_up_fixture["executable_plan"]
        ),
        outcome=ExperimentOutcome.model_validate(follow_up_fixture["outcome"]),
        target_id=cast(str, follow_up_fixture["target_id"]),
        claim_links=cast(
            dict[str, list[str]], follow_up_fixture.get("claim_links", {})
        ),
    )

    payloads = {
        "runtime-workflow-manifest": manifest_packet.model_dump(),
        "core-identification-review": identification_packet.model_dump(),
        "core-quantification-review": quant_packet.model_dump(),
        "core-ptm-review": ptm_packet.model_dump(),
        "knowledge-evidence-review": knowledge_packet.model_dump(),
        "intelligence-decision-review": intelligence_packet.model_dump(),
        "lab-review-packet": lab_packet.model_dump(),
        "lab-operational-follow-up": follow_up_packet.model_dump(),
    }

    contracts = build_workflow_stage_packet_boundary_contracts()
    assert {contract.stage_id for contract in contracts} == set(payloads)
    for contract in contracts:
        assert contract.serialization_mode is WorkflowPacketSerializationMode.MODEL_DUMP
        payload = payloads[contract.stage_id]
        assert set(contract.required_top_level_keys) <= set(payload)
