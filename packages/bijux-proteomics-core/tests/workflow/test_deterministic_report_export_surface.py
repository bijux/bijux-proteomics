# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import build_ptm_report_bundle, parse_ptm_localization_tsv
from bijux_proteomics.ptm.reporting import render_ptm_report_peptide_tsv
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    ProteomicsRunEngine,
    build_proteomics_run_bundle,
    build_tmt_label_based_report_bundle,
    render_label_based_sample_qc_tsv,
    render_proteomics_run_enrichment_tsv,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _tmt_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def _ptm_fixture(name: str) -> Path:
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


def test_flagship_enrichment_renderer_is_deterministic_under_equivalent_entry_order() -> (
    None
):
    metadata_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_proteomics_run_bundle(
        engine=ProteomicsRunEngine.FRAGPIPE,
        metadata_entries=metadata_entries,
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        report_tsv_path=_workflow_fixture("fragpipe_biological_psms.tsv"),
        contrast="control-treatment",
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture(
            "biological_report_complexes.tsv"
        ),
    )

    biological_report = report.fragpipe_workflow.biological_report
    reordered_biological_report = biological_report.model_copy(
        update={
            "go_enrichment_report": biological_report.go_enrichment_report.model_copy(
                update={
                    "term_entries": tuple(
                        reversed(biological_report.go_enrichment_report.term_entries)
                    )
                }
            ),
            "pathway_enrichment_report": biological_report.pathway_enrichment_report.model_copy(
                update={
                    "entries": tuple(
                        reversed(biological_report.pathway_enrichment_report.entries)
                    )
                }
            ),
            "complex_enrichment_report": biological_report.complex_enrichment_report.model_copy(
                update={
                    "entries": tuple(
                        reversed(biological_report.complex_enrichment_report.entries)
                    )
                }
            ),
        }
    )
    reordered_report = report.model_copy(
        update={
            "fragpipe_workflow": report.fragpipe_workflow.model_copy(
                update={"biological_report": reordered_biological_report}
            )
        }
    )

    assert render_proteomics_run_enrichment_tsv(
        report
    ) == render_proteomics_run_enrichment_tsv(reordered_report)


def test_label_based_sample_qc_renderer_is_deterministic_under_equivalent_entry_order() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(_tmt_fixture("tmt.design.tsv")).accepted_entries
    )
    report = build_tmt_label_based_report_bundle(
        _tmt_fixture("maxquant_tmt_evidence.tsv"),
        design_entries,
        control_channel="126",
    )
    reordered = report.model_copy(
        update={"sample_qc_entries": tuple(reversed(report.sample_qc_entries))}
    )

    assert render_label_based_sample_qc_tsv(report) == render_label_based_sample_qc_tsv(
        reordered
    )


def test_ptm_report_peptide_renderer_is_deterministic_under_equivalent_entry_order() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    report = build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    reordered = report.model_copy(
        update={
            "peptide_entries": tuple(
                reversed(
                    [
                        entry.model_copy(
                            update={
                                "protein_refs": tuple(reversed(entry.protein_refs)),
                                "modification_names": tuple(
                                    reversed(entry.modification_names)
                                ),
                            }
                        )
                        for entry in report.peptide_entries
                    ]
                )
            )
        }
    )

    assert render_ptm_report_peptide_tsv(report) == render_ptm_report_peptide_tsv(
        reordered
    )
