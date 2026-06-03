# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.review.flagship_kernel import (
    build_flagship_scientific_kernel_report,
)
from bijux_proteomics.review.scientific_story import WorkflowScientificSnapshot
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics_intelligence.judgment.flagship_decisions import (
    build_flagship_decision_review,
)
from bijux_proteomics_knowledge.reviews.flagship_evidence import (
    build_flagship_evidence_decision_brief,
)
from bijux_proteomics_lab.handoffs.ptm import (
    PtmLabAssayRisk,
    PtmLabValidationPacket,
    PtmLabValidationTargetEntry,
)
from bijux_proteomics_lab.reconciliation.flagship_follow_up import (
    build_flagship_workflow_follow_up_packet,
)
from bijux_proteomics_runtime.workflows.flagship_workflow_chain import (
    FlagshipWorkflowChain,
    FlagshipWorkflowStage,
    build_flagship_workflow_chain,
    compare_flagship_workflow_chains,
    evaluate_flagship_workflow_breakage,
)
from bijux_proteomics_runtime.workflows.runs import (
    DdaSearchHitInput,
    KnowledgeEvidenceInput,
    _PtmLabValidationPacketLike,
    run_dda_import_workflow_end_to_end,
    run_knowledge_review_workflow_end_to_end,
    run_lab_handoff_workflow_end_to_end,
    run_ptm_workflow_end_to_end,
    run_quant_workflow_end_to_end,
    run_sequence_to_digest_workflow_end_to_end,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _build_bundle() -> FlagshipWorkflowChain:
    sequence = run_sequence_to_digest_workflow_end_to_end(
        ">sp|P12345|PROT1 example\nMKWVTFISLLFLFSSAYSRGVFRR\n"
    )
    mgf = """BEGIN IONS
TITLE=scan=1
PEPMASS=500.2
CHARGE=2+
100.0 250.0
200.0 125.0
END IONS
BEGIN IONS
TITLE=scan=2
PEPMASS=620.3
CHARGE=2+
110.0 300.0
220.0 80.0
END IONS
"""
    dda = run_dda_import_workflow_end_to_end(
        mgf,
        search_hits=(
            DdaSearchHitInput(
                spectrum_id="scan=1",
                peptide="PEPTIDEK",
                protein_ref="P11111",
                score=42.1,
            ),
            DdaSearchHitInput(
                spectrum_id="scan=2",
                peptide="PEPTIDER",
                protein_ref="P11111",
                score=39.7,
            ),
        ),
    )
    features = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records
    quant = run_quant_workflow_end_to_end(
        features,
        design_entries=(
            ExperimentalDesignEntry(
                sample_id="C1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="c1.mzML",
                batch="B1",
            ),
            ExperimentalDesignEntry(
                sample_id="C2",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="c2.mzML",
                batch="B2",
            ),
            ExperimentalDesignEntry(
                sample_id="T1",
                condition="treated",
                replicate=1,
                fraction=1,
                spectra_file="t1.mzML",
                batch="B1",
            ),
            ExperimentalDesignEntry(
                sample_id="T2",
                condition="treated",
                replicate=2,
                fraction=1,
                spectra_file="t2.mzML",
                batch="B2",
            ),
        ),
    )
    ptm = run_ptm_workflow_end_to_end(
        _fixture_path("localization_results.tsv"),
        protein_sequences=_protein_sequences(),
        feature_records=features,
    )
    scientific_kernel = build_flagship_scientific_kernel_report(
        WorkflowScientificSnapshot(
            workflow_id="flagship-a",
            digested_peptide_count=sequence.target_peptide_count,
            identified_protein_ids=("P11111",),
            shared_peptide_group_count=0,
            quant_support_protein_ids=("P11111",),
            quant_missingness_fraction=0.25,
            quant_readiness_state="decision_ready",
            ptm_protein_ids=("P11111",),
            ambiguous_ptm_site_count=0,
            review_candidate_ids=("candidate-1",),
            target_decoy_collision_count=0,
            external_engine_disagreement_count=0,
        )
    )
    knowledge = run_knowledge_review_workflow_end_to_end(
        (
            KnowledgeEvidenceInput(
                evidence_id="E1",
                claim="PTM site S5 is condition-enriched",
                source="paper-a",
                trust_score=0.91,
            ),
            KnowledgeEvidenceInput(
                evidence_id="E2",
                claim="Protein P11111 is observed in treatment group",
                source="study-c",
                trust_score=0.82,
            ),
        )
    )
    evidence_review = build_flagship_evidence_decision_brief(
        workflow_id="flagship-a",
        artifact_path="artifacts/workflows/flagship-workflow-chain/knowledge/decision_brief.json",
        evidence_pointers=knowledge.evidence_pointers,
        accepted_claim_count=knowledge.accepted_claim_count,
        contested_claim_count=knowledge.contested_claim_count,
    )
    decision_review = build_flagship_decision_review(evidence_review, scientific_kernel)
    lab_packet = PtmLabValidationPacket(
        entries=(
            PtmLabValidationTargetEntry(
                site_key="P11111:S5:Phospho",
                target_peptides=("S[Phospho]PEPTIDEK",),
                ambiguous_site=False,
                assay_risk=PtmLabAssayRisk.LOW,
                recommended_controls=("matrix_control",),
                evidence_needs=("site_localization_fragments",),
            ),
        ),
        unresolved_risk_count=0,
    )
    lab_handoff = run_lab_handoff_workflow_end_to_end(
        cast(_PtmLabValidationPacketLike, lab_packet)
    )
    follow_up = build_flagship_workflow_follow_up_packet(
        decision_review,
        planned_assay_count=lab_handoff.planned_assay_count,
        export_file_count=lab_handoff.export_file_count,
        unresolved_risk_count=lab_handoff.unresolved_risk_count,
    )
    return build_flagship_workflow_chain(
        sequence_report=sequence,
        dda_report=dda,
        quant_report=quant,
        ptm_report=ptm,
        scientific_kernel=scientific_kernel,
        evidence_review=evidence_review,
        decision_review=decision_review,
        lab_handoff=lab_handoff,
        follow_up=follow_up,
    )


def test_build_flagship_workflow_chain_tracks_all_owner_stages() -> None:
    bundle = _build_bundle()

    assert bundle.proof_complete is True
    assert {stage.stage for stage in bundle.stages} == set(FlagshipWorkflowStage)
    assert bundle.scope_dossier.approved_workflow_families == ("flagship-workflows",)
    assert all(
        claim.artifact_path.startswith("artifacts/") for claim in bundle.artifact_claims
    )


def test_compare_flagship_workflow_chains_is_deterministic_for_same_inputs() -> None:
    first = _build_bundle()
    second = _build_bundle()

    report = compare_flagship_workflow_chains(first, second)

    assert report.equivalent is True
    assert report.changed_fields == ()


def test_evaluate_flagship_workflow_breakage_detects_missing_follow_up_and_bad_paths() -> (
    None
):
    bundle = _build_bundle()
    broken = bundle.model_copy(
        update={
            "stages": tuple(
                stage
                for stage in bundle.stages
                if stage.stage is not FlagshipWorkflowStage.FOLLOW_UP
            ),
            "artifact_claims": (
                bundle.artifact_claims[0].model_copy(
                    update={"artifact_path": "/tmp/not-allowed.json"}
                ),
                *bundle.artifact_claims[1:],
            ),
        }
    )

    report = evaluate_flagship_workflow_breakage(broken)

    assert report.valid is False
    assert {finding.code for finding in report.findings} == {
        "missing_owner_stage",
        "artifact_path_outside_artifacts",
    }
