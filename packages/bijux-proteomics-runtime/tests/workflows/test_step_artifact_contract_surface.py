# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics_lab.handoffs.ptm import (
    PtmLabAssayRisk,
    PtmLabValidationPacket,
    PtmLabValidationTargetEntry,
)
from bijux_proteomics_runtime.artifacts import StepArtifact
from bijux_proteomics_runtime.workflows.runs import (
    DdaSearchHitInput,
    DiaPrecursorQuantInput,
    KnowledgeEvidenceInput,
    _PtmLabValidationPacketLike,
    run_dda_import_workflow_end_to_end,
    run_dia_import_workflow_end_to_end,
    run_knowledge_review_workflow_end_to_end,
    run_lab_handoff_workflow_end_to_end,
    run_multiplex_workflow_end_to_end,
    run_ptm_workflow_end_to_end,
    run_quant_workflow_end_to_end,
    run_sequence_to_digest_workflow_end_to_end,
    run_targeted_workflow_end_to_end,
)


def _runtime_fixture_path(*parts: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / Path(*parts)


def _quant_design_entries() -> tuple[ExperimentalDesignEntry, ...]:
    return (
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
            multiplex_group="plex-a",
            multiplex_channel="127C",
        ),
        ExperimentalDesignEntry(
            sample_id="T1",
            condition="treated",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzML",
            batch="B1",
            multiplex_group="plex-a",
            multiplex_channel="126",
        ),
        ExperimentalDesignEntry(
            sample_id="T2",
            condition="treated",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzML",
            batch="B2",
            multiplex_group="plex-a",
            multiplex_channel="128N",
        ),
    )


def _ptm_protein_sequences() -> dict[str, str]:
    report = parse_fasta_document(
        _runtime_fixture_path("fasta", "ptm_sites.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _lab_packet() -> _PtmLabValidationPacketLike:
    packet = PtmLabValidationPacket(
        entries=(
            PtmLabValidationTargetEntry(
                site_key="P11111:S5:Phospho",
                target_peptides=("S[Phospho]PEPTIDEK",),
                ambiguous_site=False,
                assay_risk=PtmLabAssayRisk.LOW,
                recommended_controls=("matrix_control",),
                evidence_needs=("site_localization_fragments",),
            ),
            PtmLabValidationTargetEntry(
                site_key="P22222:T9:Phospho",
                target_peptides=("T[Phospho]IDEK",),
                ambiguous_site=True,
                assay_risk=PtmLabAssayRisk.HIGH,
                recommended_controls=("co_localization_control",),
                evidence_needs=("orthogonal_confirmation",),
            ),
        ),
        unresolved_risk_count=1,
    )
    return cast(_PtmLabValidationPacketLike, packet)


def test_every_runtime_workflow_step_uses_step_artifact_contract(
    tmp_path: Path,
) -> None:
    features = parse_ms1_feature_table(
        _runtime_fixture_path("ptm", "ptm_features.tsv")
    ).accepted_records
    targeted_qc_path = tmp_path / "chromatogram_qc.tsv"
    targeted_qc_path.write_text(
        "\n".join(
            (
                "run_id\tscan_time_seconds\ttic\tbpc",
                "run_01\t0.0\t10234.0\t812.0",
                "run_01\t5.0\t9950.5\t780.0",
            )
        ),
        encoding="utf-8",
    )

    reports = (
        run_sequence_to_digest_workflow_end_to_end(
            ">sp|P12345|PROT1 example\nMKWVTFISLLFLFSSAYSRGVFRR"
        ),
        run_dda_import_workflow_end_to_end(
            """BEGIN IONS
TITLE=scan=1
PEPMASS=500.2
CHARGE=2+
100.0 250.0
END IONS
""",
            search_hits=(
                DdaSearchHitInput(
                    spectrum_id="scan=1",
                    peptide="PEPTIDEK",
                    protein_ref="P11111",
                    score=42.1,
                ),
            ),
        ),
        run_dia_import_workflow_end_to_end(
            (
                DiaPrecursorQuantInput(
                    precursor_id="P1_2",
                    peptide="PEPTIDEK",
                    protein_ref="P11111",
                    sample_id="S1",
                    intensity=1200.0,
                ),
                DiaPrecursorQuantInput(
                    precursor_id="P2_2",
                    peptide="PEPTIDER",
                    protein_ref="Q22222",
                    sample_id="S2",
                    intensity=None,
                ),
            )
        ),
        run_quant_workflow_end_to_end(features, design_entries=_quant_design_entries()),
        run_ptm_workflow_end_to_end(
            _runtime_fixture_path("ptm", "localization_results.tsv"),
            protein_sequences=_ptm_protein_sequences(),
            feature_records=features,
        ),
        run_multiplex_workflow_end_to_end(
            features,
            design_entries=_quant_design_entries(),
        ),
        run_targeted_workflow_end_to_end(
            targeted_qc_path,
            supported_follow_up_payload={
                "transition_review": {
                    "approved_transition_ids": ["tr-1"],
                    "exploratory_transition_ids": ["tr-2"],
                },
                "outcome": {"assay_outcomes": [{"transition_id": "tr-1"}]},
            },
            failed_follow_up_payload={
                "transition_review": {"refused_transition_ids": ["tr-3"]},
                "workflow_readiness_summary": {"ready": False},
            },
            refused_follow_up_payload={
                "workflow_readiness_summary": {"ready": False},
            },
        ),
        run_knowledge_review_workflow_end_to_end(
            (
                KnowledgeEvidenceInput(
                    evidence_id="E1",
                    claim="site increases",
                    source="paper-a",
                    trust_score=0.9,
                    contradicts=("E2",),
                ),
                KnowledgeEvidenceInput(
                    evidence_id="E2",
                    claim="site unchanged",
                    source="paper-b",
                    trust_score=0.6,
                    contradicts=("E1",),
                ),
            )
        ),
        run_lab_handoff_workflow_end_to_end(_lab_packet()),
    )

    for report in reports:
        assert report.steps
        assert all(isinstance(step, StepArtifact) for step in report.steps)
        for step in report.steps:
            assert step.input_checksums
            assert step.output_checksums
            assert step.entity_counts
            assert step.schema_names
            assert "output_count" not in step.to_dict()


def test_refused_sequence_step_records_allowed_empty_reason() -> None:
    report = run_sequence_to_digest_workflow_end_to_end("not a fasta document")

    assert report.status.value == "refused"
    assert len(report.steps) == 1
    assert report.steps[0].entity_counts == {"accepted_records": 0}
    assert report.steps[0].allowed_empty_reason
