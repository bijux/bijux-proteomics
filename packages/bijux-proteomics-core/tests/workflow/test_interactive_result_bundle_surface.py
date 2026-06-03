# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.io.formats.proteomics_formats import ExperimentalDesignEntry
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
    build_biological_result_report_bundle,
    build_interactive_result_bundle_from_artifacts,
    export_biological_result_report_bundle,
    render_interactive_result_bundle_summary_tsv,
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


def _ptm_design_entries() -> tuple[ExperimentalDesignEntry, ...]:
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


def test_interactive_result_bundle_preserves_real_report_surfaces(
    tmp_path: Path,
) -> None:
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

    bundle = build_interactive_result_bundle_from_artifacts(
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
        run_qc_assessment_tsv_paths=(qc_path,),
    )

    assert bundle.summary.biological_report_available is True
    assert bundle.summary.ptm_report_available is True
    assert bundle.summary.run_qc_input_count == 1
    assert bundle.summary.sample_count >= 6
    assert bundle.summary.protein_count >= 3
    assert bundle.summary.peptide_count >= 10
    assert bundle.summary.ptm_site_count >= 3
    assert bundle.summary.pathway_count >= 1
    assert bundle.summary.qc_entry_count >= 2
    assert bundle.summary.card_count >= 6
    assert bundle.summary.graph_node_count >= 1
    assert bundle.summary.graph_edge_count >= 1
    assert bundle.summary.plot_count >= 5
    assert {report.manifest_json for report in bundle.source_reports} == {
        "biological_report_manifest.json",
        "ptm_report_manifest.json",
    }
    assert any(sample.sample_id == "T2" for sample in bundle.samples)
    assert any(
        peptide.source_surface == "ptm_peptides" and peptide.site_keys
        for peptide in bundle.peptides
    )
    assert any(site.claim_ids for site in bundle.ptm_sites)
    assert any(pathway.supporting_protein_refs for pathway in bundle.pathways)
    assert any(card.card_kind.value == "protein_evidence" for card in bundle.cards)
    assert any(card.card_kind.value == "ptm_evidence" for card in bundle.cards)
    assert any(
        plot.plot_kind.value == "biological_volcano_json" for plot in bundle.plots
    )
    assert "sample_count" in render_interactive_result_bundle_summary_tsv(bundle)
