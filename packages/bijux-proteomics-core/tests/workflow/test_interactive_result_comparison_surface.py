# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_report_bundle,
    export_ptm_report_bundle,
    parse_ptm_localization_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    InteractiveResultBundle,
    InteractiveResultBundleSummary,
    InteractiveResultComparisonReasonCode,
    InteractiveResultPathway,
    InteractiveResultProtein,
    InteractiveResultPtmSite,
    InteractiveResultQcEntry,
    InteractiveResultQcKind,
    InteractiveResultSourceKind,
    InteractiveResultSourceReport,
    build_biological_result_report_bundle,
    build_interactive_result_comparison_from_artifacts,
    build_interactive_result_comparison_payload,
    export_biological_result_report_bundle,
    render_interactive_result_comparison_pathway_tsv,
    render_interactive_result_comparison_protein_tsv,
    render_interactive_result_comparison_ptm_site_tsv,
    render_interactive_result_comparison_qc_tsv,
    render_interactive_result_comparison_summary_tsv,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _protein_sequences() -> dict[str, str]:
    report = parse_fasta_document(
        _fasta_fixture("ptm_sites.fasta").read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _ptm_design_entries():
    return tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )


def _write_run_qc_tsv(
    path: Path,
    *,
    qc_status: str,
    reason_codes: str,
    severity: str,
    message: str,
) -> None:
    path.write_text(
        "\n".join(
            (
                "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                (
                    "run\tt2.mzml\t"
                    f"{qc_status}\t{reason_codes}\tidentification_rate\tIdentification rate\t0.05\tfraction\t"
                    f"{severity}\tblock\ttrue\t{message}"
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _rewrite_first_tsv_row(path: Path, updates: dict[str, str]) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path.name!r} must include a header row")
        rows = list(reader)
        if not rows:
            raise ValueError(f"{path.name!r} must include at least one data row")
        rows[0].update(updates)
        fieldnames = list(reader.fieldnames)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _build_minimal_bundle(
    *,
    report_dir: str,
    protein_log2_fold_change: float,
    protein_evidence_tier: str,
    ptm_correction_status: str,
    qc_status: str,
    pathway_enrichment_ratio: float,
) -> InteractiveResultBundle:
    return InteractiveResultBundle(
        source_reports=(
            InteractiveResultSourceReport(
                source_kind=InteractiveResultSourceKind.BIOLOGICAL_REPORT,
                report_dir=report_dir,
            ),
        ),
        summary=InteractiveResultBundleSummary(
            biological_report_available=True,
            ptm_report_available=True,
            run_qc_input_count=1,
            sample_count=2,
            protein_count=1,
            peptide_count=1,
            ptm_site_count=1,
            pathway_count=1,
            qc_entry_count=1,
            card_count=0,
            graph_node_count=0,
            graph_edge_count=0,
            plot_count=0,
        ),
        proteins=(
            InteractiveResultProtein(
                object_id="protein:pg-P04637",
                protein_group_id="pg-P04637",
                representative_protein_ref="P04637",
                protein_refs=("P04637",),
                gene_symbol="SIGA",
                condition_a="control",
                condition_b="treatment",
                log2_fold_change=protein_log2_fold_change,
                adjusted_p_value=0.01,
                significant=True,
                evidence_tier=protein_evidence_tier,
                peptide_ids=("protein-peptide:pg-P04637:PEPTIDEK",),
                pathway_ids=("custom:stress",),
                ptm_site_keys=("P11111:S5:Phospho",),
                warning_codes=(),
                graph_node_ids=(),
                source_reports=(InteractiveResultSourceKind.BIOLOGICAL_REPORT,),
            ),
        ),
        peptides=(),
        ptm_sites=(
            InteractiveResultPtmSite(
                site_key="P11111:S5:Phospho",
                protein_ref="P11111",
                residue="S",
                position=5,
                modification_name="Phospho",
                localization_tier="localized",
                adjusted_p_value=0.02,
                log2_fold_change=1.3,
                corrected_log2_fold_change=0.9,
                protein_correction_status=ptm_correction_status,
                mechanism_class="activation_linked",
                warning_codes=(),
                claim_ids=("claim:ptm:1",),
                sample_ids=("T1",),
            ),
        ),
        pathways=(
            InteractiveResultPathway(
                pathway_id="custom:stress",
                pathway_name="Stress response pathway",
                source_name="custom",
                source_accession="custom:stress",
                condition_a="control",
                condition_b="treatment",
                comparison_confidence_status="supported",
                activity_score_delta=1.2,
                enrichment_ratio=pathway_enrichment_ratio,
                adjusted_p_value=0.03,
                foreground_overlap_count=2,
                supporting_protein_refs=("P04637",),
                unresolved_member_ids=(),
            ),
        ),
        qc_entries=(
            InteractiveResultQcEntry(
                qc_id="section_confidence:biological_hypotheses",
                qc_kind=InteractiveResultQcKind.SECTION_CONFIDENCE,
                scope="section",
                entity_id="biological_hypotheses",
                status=qc_status,
                severity=qc_status,
                reason_codes=(),
                message="section confidence changed",
                source_surface="biological_report_section_confidence",
            ),
        ),
        cards=(),
        graph_nodes=(),
        graph_edges=(),
        plots=(),
        note="minimal bundle for comparison testing",
    )


def _build_real_artifact_pair(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, Path, Path]:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    biological_report = build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture(
            "biological_report_complexes.tsv"
        ),
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    ptm_evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    ptm_features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    ptm_annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
    )
    ptm_report = build_ptm_report_bundle(
        ptm_evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=ptm_features.accepted_records,
        design_entries=_ptm_design_entries(),
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        condition_a="control",
        condition_b="treated",
        annotation_records=ptm_annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )

    left_biological_dir = tmp_path / "left_biological_report"
    right_biological_dir = tmp_path / "right_biological_report"
    left_ptm_dir = tmp_path / "left_ptm_report"
    right_ptm_dir = tmp_path / "right_ptm_report"

    left_biological_manifest = export_biological_result_report_bundle(
        biological_report,
        left_biological_dir,
    )
    (left_biological_dir / "biological_report_manifest.json").write_text(
        left_biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    right_biological_manifest = export_biological_result_report_bundle(
        biological_report,
        right_biological_dir,
    )
    (right_biological_dir / "biological_report_manifest.json").write_text(
        right_biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    left_ptm_manifest = export_ptm_report_bundle(ptm_report, left_ptm_dir)
    (left_ptm_dir / "ptm_report_manifest.json").write_text(
        left_ptm_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    right_ptm_manifest = export_ptm_report_bundle(ptm_report, right_ptm_dir)
    (right_ptm_dir / "ptm_report_manifest.json").write_text(
        right_ptm_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    _rewrite_first_tsv_row(
        right_biological_dir / "biological_protein_cards.tsv",
        {"log2_fold_change": "9.5", "evidence_tier": "exploratory"},
    )
    _rewrite_first_tsv_row(
        right_biological_dir / "biological_report_section_confidence.tsv",
        {
            "confidence_label": "invalid",
            "rationale": "comparison side was downgraded by QC review",
        },
    )
    _rewrite_first_tsv_row(
        right_biological_dir / "biological_pathway_entries.tsv",
        {"enrichment_ratio": "0.95", "adjusted_p_value": "0.8"},
    )
    _rewrite_first_tsv_row(
        right_ptm_dir / "ptm_evidence_cards.tsv",
        {
            "protein_correction_status": "uncorrected",
            "mechanism_class": "rewired_signaling",
        },
    )

    left_qc_path = tmp_path / "left_run_qc.tsv"
    right_qc_path = tmp_path / "right_run_qc.tsv"
    _write_run_qc_tsv(
        left_qc_path,
        qc_status="fail",
        reason_codes="identification_rate_low",
        severity="failed",
        message="left run failed QC",
    )
    _write_run_qc_tsv(
        right_qc_path,
        qc_status="pass",
        reason_codes="",
        severity="passed",
        message="right run passed QC",
    )
    return (
        left_biological_dir,
        left_ptm_dir,
        left_qc_path,
        right_biological_dir,
        right_ptm_dir,
        right_qc_path,
    )


def test_interactive_result_comparison_payload_preserves_changed_entities_and_reasons() -> (
    None
):
    left_bundle = _build_minimal_bundle(
        report_dir="left",
        protein_log2_fold_change=1.2,
        protein_evidence_tier="supported",
        ptm_correction_status="corrected",
        qc_status="high",
        pathway_enrichment_ratio=0.2,
    )
    right_bundle = _build_minimal_bundle(
        report_dir="right",
        protein_log2_fold_change=2.4,
        protein_evidence_tier="exploratory",
        ptm_correction_status="uncorrected",
        qc_status="invalid",
        pathway_enrichment_ratio=0.8,
    )

    payload = build_interactive_result_comparison_payload(left_bundle, right_bundle)

    assert payload.summary.changed_protein_count == 1
    assert payload.summary.changed_ptm_site_count == 1
    assert payload.summary.changed_qc_entry_count == 1
    assert payload.summary.changed_pathway_count == 1
    assert {reason.code for reason in payload.changed_proteins[0].reasons} >= {
        InteractiveResultComparisonReasonCode.LOG2_FOLD_CHANGE_CHANGED,
        InteractiveResultComparisonReasonCode.EVIDENCE_TIER_CHANGED,
    }
    assert {reason.code for reason in payload.changed_ptm_sites[0].reasons} >= {
        InteractiveResultComparisonReasonCode.PROTEIN_CORRECTION_STATUS_CHANGED,
    }
    assert {reason.code for reason in payload.changed_qc_entries[0].reasons} >= {
        InteractiveResultComparisonReasonCode.QC_STATUS_CHANGED,
        InteractiveResultComparisonReasonCode.QC_SEVERITY_CHANGED,
    }
    assert {reason.code for reason in payload.changed_pathways[0].reasons} >= {
        InteractiveResultComparisonReasonCode.ENRICHMENT_RATIO_CHANGED,
    }
    assert "changed_protein_count" in render_interactive_result_comparison_summary_tsv(
        payload
    )
    assert "reasons" in render_interactive_result_comparison_protein_tsv(payload)
    assert (
        "protein_correction_status"
        in render_interactive_result_comparison_ptm_site_tsv(payload)
    )
    assert "qc_id" in render_interactive_result_comparison_qc_tsv(payload)
    assert "pathway_id" in render_interactive_result_comparison_pathway_tsv(payload)


def test_interactive_result_comparison_from_artifacts_detects_changed_result_objects(
    tmp_path: Path,
) -> None:
    (
        left_biological_dir,
        left_ptm_dir,
        left_qc_path,
        right_biological_dir,
        right_ptm_dir,
        right_qc_path,
    ) = _build_real_artifact_pair(tmp_path)

    payload = build_interactive_result_comparison_from_artifacts(
        left_biological_report_dir=left_biological_dir,
        left_ptm_report_dir=left_ptm_dir,
        left_run_qc_assessment_tsv_paths=(left_qc_path,),
        right_biological_report_dir=right_biological_dir,
        right_ptm_report_dir=right_ptm_dir,
        right_run_qc_assessment_tsv_paths=(right_qc_path,),
    )

    assert payload.summary.changed_protein_count >= 1
    assert payload.summary.changed_ptm_site_count >= 1
    assert payload.summary.changed_qc_entry_count >= 2
    assert payload.summary.changed_pathway_count >= 1
    assert any(
        reason.code is InteractiveResultComparisonReasonCode.EVIDENCE_TIER_CHANGED
        for entry in payload.changed_proteins
        for reason in entry.reasons
    )
    assert any(
        reason.code
        is InteractiveResultComparisonReasonCode.PROTEIN_CORRECTION_STATUS_CHANGED
        for entry in payload.changed_ptm_sites
        for reason in entry.reasons
    )
    assert any(
        reason.code is InteractiveResultComparisonReasonCode.QC_STATUS_CHANGED
        for entry in payload.changed_qc_entries
        for reason in entry.reasons
    )
    assert any(
        reason.code is InteractiveResultComparisonReasonCode.ENRICHMENT_RATIO_CHANGED
        for entry in payload.changed_pathways
        for reason in entry.reasons
    )
