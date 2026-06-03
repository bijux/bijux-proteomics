# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    MissingValueKind,
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    QuantEntityLevel,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
    PeptideIntensityMatrixRow,
    PeptideIntensityMatrixSummary,
    PeptideIntensityMatrixValue,
    PeptideMatrixGroupingMode,
    PeptideMatrixSourceKind,
)
from bijux_proteomics.quantification.protein_intensity_matrix import (
    ProteinIntensityMatrixReport,
    ProteinIntensityMatrixRow,
    ProteinIntensityMatrixSummary,
    ProteinIntensityMatrixValue,
    ProteinMatrixTargetKind,
)
from bijux_proteomics.quantification.protein_lfq import (
    ProteinLfqReport,
    ProteinLfqRow,
    ProteinLfqSummary,
    ProteinLfqValue,
)


def test_experimental_design_entries_convert_to_sample_metadata() -> None:
    entry = ExperimentalDesignEntry(
        sample_id="sample-a",
        condition="control",
        replicate=1,
        fraction=1,
        spectra_file="run-a",
        batch="batch-1",
        multiplex_group="plex-1",
        multiplex_channel="126",
    )

    sample_metadata = entry.to_domain_record()

    assert sample_metadata.run_id == "run-a"
    assert sample_metadata.plex_id == "plex-1"
    assert sample_metadata.channel == "126"


def test_peptide_and_protein_reports_convert_to_quant_matrices() -> None:
    sample_metadata = (
        ExperimentalDesignEntry(
            sample_id="sample-a",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="run-a",
        ).to_domain_record(),
        ExperimentalDesignEntry(
            sample_id="sample-b",
            condition="treated",
            replicate=1,
            fraction=1,
            spectra_file="run-b",
        ).to_domain_record(),
    )
    missing_summary = MissingValueSummaryReport(
        entity_level=QuantEntityLevel.PEPTIDE,
        policy=MissingValueSummaryPolicy(),
        entries=(
            MissingValueSummaryEntry(
                sample_id="sample-a",
                observed_count=1,
                zero_count=0,
                not_observed_count=0,
                filtered_count=0,
            ),
            MissingValueSummaryEntry(
                sample_id="sample-b",
                observed_count=0,
                zero_count=0,
                not_observed_count=1,
                filtered_count=0,
            ),
        ),
        included_entity_ids=("PEPTIDE",),
        excluded_entity_ids=(),
    )
    peptide_report = PeptideIntensityMatrixReport(
        source_kind=PeptideMatrixSourceKind.PSM,
        grouping_mode=PeptideMatrixGroupingMode.PEPTIDE_SEQUENCE,
        aggregation_method=QuantRollupMethod.SUM,
        sample_ids=("sample-a", "sample-b"),
        rows=(
            PeptideIntensityMatrixRow(
                entity_id="PEPTIDE",
                peptide_sequence="PEPTIDE",
                modified_peptides=("PEPTIDE",),
                charge_states=(2,),
                protein_refs=("P001",),
                values=(
                    PeptideIntensityMatrixValue(
                        sample_id="sample-a",
                        abundance=10.0,
                        missing_value_kind=MissingValueKind.OBSERVED,
                        source_record_count=1,
                    ),
                    PeptideIntensityMatrixValue(
                        sample_id="sample-b",
                        abundance=None,
                        missing_value_kind=MissingValueKind.NOT_OBSERVED,
                        source_record_count=0,
                    ),
                ),
            ),
        ),
        missing_summary=missing_summary,
        summary=PeptideIntensityMatrixSummary(
            accepted_source_record_count=1,
            skipped_source_record_count=0,
            sample_count=2,
            peptide_row_count=1,
            observed_cell_count=1,
            zero_cell_count=0,
            missing_cell_count=1,
            filtered_cell_count=0,
        ),
        note="peptide note",
    )
    protein_report = ProteinIntensityMatrixReport(
        source_kind=PeptideMatrixSourceKind.PSM,
        grouping_mode=PeptideMatrixGroupingMode.PEPTIDE_SEQUENCE,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
        sample_ids=("sample-a", "sample-b"),
        rows=(
            ProteinIntensityMatrixRow(
                entity_id="P001",
                target_kind=ProteinMatrixTargetKind.PROTEIN,
                protein_refs=("P001",),
                peptide_count=1,
                unique_peptide_count=1,
                shared_peptide_count=0,
                contributing_peptides=("PEPTIDE",),
                values=(
                    ProteinIntensityMatrixValue(
                        sample_id="sample-a",
                        abundance=10.0,
                        missing_value_kind=MissingValueKind.OBSERVED,
                        contributing_peptide_count=1,
                    ),
                    ProteinIntensityMatrixValue(
                        sample_id="sample-b",
                        abundance=None,
                        missing_value_kind=MissingValueKind.NOT_OBSERVED,
                        contributing_peptide_count=0,
                    ),
                ),
            ),
        ),
        missing_summary=missing_summary,
        summary=ProteinIntensityMatrixSummary(
            peptide_row_count=1,
            protein_row_count=1,
            sample_count=2,
            unique_only=False,
            observed_cell_count=1,
            zero_cell_count=0,
            missing_cell_count=1,
            filtered_cell_count=0,
        ),
        note="protein note",
    )

    peptide_matrix = peptide_report.to_quant_matrix(sample_metadata=sample_metadata)
    protein_matrix = protein_report.to_quant_matrix(sample_metadata=sample_metadata)

    assert peptide_matrix.entity_ids == ("PEPTIDE",)
    assert peptide_matrix.sample_metadata[1].sample_id == "sample-b"
    assert peptide_matrix.support_counts == ((1, 0),)
    assert protein_matrix.entity_ids == ("P001",)
    assert protein_matrix.support_counts == ((1, 0),)
    assert protein_matrix.row_metadata[0]["target_kind"] == "protein"


def test_protein_lfq_reports_convert_to_quant_matrices() -> None:
    report = ProteinLfqReport(
        source_kind=PeptideMatrixSourceKind.PSM,
        grouping_mode=PeptideMatrixGroupingMode.PEPTIDE_SEQUENCE,
        target_kind=ProteinMatrixTargetKind.PROTEIN_GROUP,
        aggregation_method=QuantRollupMethod.SUM,
        minimum_shared_peptides=1,
        sample_ids=("sample-a",),
        rows=(
            ProteinLfqRow(
                entity_id="P001;P002",
                target_kind=ProteinMatrixTargetKind.PROTEIN_GROUP,
                protein_refs=("P001", "P002"),
                peptide_count=2,
                unique_peptide_count=1,
                shared_peptide_count=1,
                pairwise_ratio_count=0,
                connected_component_count=1,
                fully_connected=True,
                contributing_peptides=("PEPTIDE", "SECOND"),
                values=(
                    ProteinLfqValue(
                        sample_id="sample-a",
                        abundance=11.0,
                        log2_abundance=3.46,
                        missing_value_kind=MissingValueKind.OBSERVED,
                        contributing_peptide_count=2,
                    ),
                ),
            ),
        ),
        missing_summary=MissingValueSummaryReport(
            entity_level=QuantEntityLevel.PROTEIN,
            policy=MissingValueSummaryPolicy(),
            entries=(
                MissingValueSummaryEntry(
                    sample_id="sample-a",
                    observed_count=1,
                    zero_count=0,
                    not_observed_count=0,
                    filtered_count=0,
                ),
            ),
            included_entity_ids=("P001;P002",),
            excluded_entity_ids=(),
        ),
        summary=ProteinLfqSummary(
            peptide_row_count=2,
            protein_row_count=1,
            sample_count=1,
            unique_only=False,
            minimum_shared_peptides=1,
            fully_connected_row_count=1,
            disconnected_row_count=0,
            total_pairwise_ratio_count=0,
            observed_cell_count=1,
            missing_cell_count=0,
        ),
        note="lfq note",
    )

    matrix = report.to_quant_matrix()

    assert matrix.entity_ids == ("P001;P002",)
    assert matrix.values[0][0] == 11.0
    assert matrix.support_counts == ((2,),)
    assert matrix.row_metadata[0]["fully_connected"] == "true"
