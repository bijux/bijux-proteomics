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
from bijux_proteomics.review import (
    CompactResultSummarySectionKind,
    build_compact_result_summary_report_from_artifacts,
    render_compact_result_summary_entry_tsv,
    render_compact_result_summary_markdown,
    render_compact_result_summary_overview_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    export_biological_result_report_bundle,
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


def _write_run_qc_tsv(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                "run\tt2.mzml\tfail\tidentification_rate_low\tidentification_rate\tIdentification rate\t0.05\tfraction\tfailed\tblock\ttrue\tidentification rate fell below enforced threshold",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _build_real_summary_artifacts(tmp_path: Path) -> tuple[Path, Path, Path]:
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
    biological_dir = tmp_path / "biological_report"
    biological_manifest = export_biological_result_report_bundle(
        biological_report,
        biological_dir,
    )
    (biological_dir / "biological_report_manifest.json").write_text(
        biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
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
    ptm_dir = tmp_path / "ptm_report"
    ptm_manifest = export_ptm_report_bundle(ptm_report, ptm_dir)
    (ptm_dir / "ptm_report_manifest.json").write_text(
        ptm_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    qc_path = tmp_path / "run_qc.tsv"
    _write_run_qc_tsv(qc_path)
    return biological_dir, ptm_dir, qc_path


def test_compact_result_summary_preserves_required_sections_and_validated_sources(
    tmp_path: Path,
) -> None:
    biological_dir, ptm_dir, qc_path = _build_real_summary_artifacts(tmp_path)

    report = build_compact_result_summary_report_from_artifacts(
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
        run_qc_assessment_tsv_paths=(qc_path,),
    )

    by_section = {section.section_kind: section for section in report.sections}
    assert tuple(by_section) == (
        CompactResultSummarySectionKind.SAMPLE_QC,
        CompactResultSummarySectionKind.STRONGEST_FINDINGS,
        CompactResultSummarySectionKind.WEAK_FINDINGS,
        CompactResultSummarySectionKind.FAILED_ASSUMPTIONS,
        CompactResultSummarySectionKind.NEXT_VALIDATION_TARGETS,
    )
    strongest = by_section[CompactResultSummarySectionKind.STRONGEST_FINDINGS]
    weak = by_section[CompactResultSummarySectionKind.WEAK_FINDINGS]
    failed = by_section[CompactResultSummarySectionKind.FAILED_ASSUMPTIONS]
    next_targets = by_section[CompactResultSummarySectionKind.NEXT_VALIDATION_TARGETS]

    assert strongest.entries
    assert all(
        entry.result_surfaces == ("biological_supported_claims",)
        for entry in strongest.entries
    )
    assert weak.entries
    assert all(
        entry.result_surfaces[0]
        in {
            "biological_hypotheses",
            "biological_report_section_confidence",
        }
        for entry in weak.entries
    )
    assert failed.entries
    assert all(
        entry.result_surfaces[0]
        in {
            "biological_rejected_claims",
            "biological_report_section_confidence",
        }
        for entry in failed.entries
    )
    assert next_targets.entries
    assert all(entry.result_surfaces for entry in next_targets.entries)

    strongest_row_ids = {
        row_id for entry in strongest.entries for row_id in entry.result_row_ids
    }
    assert "Strongest findings" in render_compact_result_summary_markdown(report)
    assert "Sample QC" in render_compact_result_summary_markdown(report)
    assert "entry_count" in render_compact_result_summary_overview_tsv(report)
    assert "summary_text" in render_compact_result_summary_entry_tsv(report)
    assert strongest_row_ids


def test_compact_result_summary_does_not_mix_supported_and_rejected_claim_rows(
    tmp_path: Path,
) -> None:
    biological_dir, ptm_dir, qc_path = _build_real_summary_artifacts(tmp_path)

    report = build_compact_result_summary_report_from_artifacts(
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
        run_qc_assessment_tsv_paths=(qc_path,),
    )

    strongest_row_ids = {
        row_id
        for section in report.sections
        if section.section_kind is CompactResultSummarySectionKind.STRONGEST_FINDINGS
        for entry in section.entries
        for row_id in entry.result_row_ids
    }
    with (biological_dir / "biological_rejected_claims.tsv").open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        rejected_claim_ids = {
            row["claim_id"] for row in csv.DictReader(handle, delimiter="\t")
        }
    assert strongest_row_ids.isdisjoint(rejected_claim_ids)
