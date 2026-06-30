# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""FragPipe bundle import over PSM, peptide, and protein evidence tables."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.adapters.fragpipe_import.evidence_tables import (
    build_fragpipe_open_search_evidence,
    parse_fragpipe_peptide_table,
    parse_fragpipe_protein_table,
    parse_fragpipe_quant_table,
)
from bijux_proteomics.identification.contracts import (
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics.identification.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
    build_rejected_evidence_rows_from_psm_rows,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterKind,
)
from bijux_proteomics.identification.search_adapters.normalization import (
    normalize_search_results_with_adapter,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.identification.adapters.fragpipe_import.models import (
    FragpipeCanonicalPsmEntry,
    FragpipeImportReport,
    FragpipeImportSummary,
    FragpipePsmReviewEntry,
)
from bijux_proteomics.identification.adapters.fragpipe_import.psm_rows import (
    build_fragpipe_canonical_psm_rows,
    build_fragpipe_psm_rows,
)
from bijux_proteomics.identification.adapters.fragpipe_import.rendering import (
    render_fragpipe_canonical_psm_tsv,
    render_fragpipe_open_search_evidence_tsv,
    render_fragpipe_peptide_tsv,
    render_fragpipe_protein_quantity_tsv,
    render_fragpipe_protein_tsv,
    render_fragpipe_psm_tsv,
    render_fragpipe_summary_tsv,
)
from bijux_proteomics.identification.adapters.fragpipe_import.table_support import (
    has_modified_content,
)


def build_fragpipe_import_report(
    psm_tsv_path: Path,
    *,
    peptide_tsv_path: Path,
    protein_tsv_path: Path,
    quant_tsv_path: Path | None = None,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
    open_search_mass_tolerance: float = 0.01,
) -> FragpipeImportReport:
    """Import one FragPipe result bundle with explicit table preservation."""
    if open_search_mass_tolerance < 0:
        raise ValueError("open_search_mass_tolerance must be non-negative")
    active_decoy_policy = decoy_policy or TargetDecoyLabelPolicy(
        protein_prefix="DECOY_"
    )
    psm_normalization = normalize_search_results_with_adapter(
        source_path=psm_tsv_path,
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        dialect_id="fragpipe-psm",
    )
    canonical_psms = build_fragpipe_canonical_psm_rows(
        normalization_report=psm_normalization,
        open_search_mass_tolerance=open_search_mass_tolerance,
    )
    psm_rows = build_fragpipe_psm_rows(
        normalization_report=psm_normalization,
        open_search_mass_tolerance=open_search_mass_tolerance,
    )
    peptide_rows = parse_fragpipe_peptide_table(
        peptide_tsv_path,
        decoy_policy=active_decoy_policy,
        open_search_mass_tolerance=open_search_mass_tolerance,
    )
    protein_rows = parse_fragpipe_protein_table(
        protein_tsv_path,
        decoy_policy=active_decoy_policy,
    )
    open_search_evidence = build_fragpipe_open_search_evidence(
        canonical_psms=canonical_psms,
        peptide_rows=peptide_rows,
    )
    protein_quantity_rows = parse_fragpipe_quant_table(
        quant_tsv_path,
        decoy_policy=active_decoy_policy,
    )
    protein_refs = {
        protein_ref
        for row in peptide_rows
        for protein_ref in row.protein_refs + row.mapped_protein_refs
    }
    summary = FragpipeImportSummary(
        accepted_psm_count=len(psm_rows),
        rejected_psm_count=len(psm_normalization.parse_report.rejected_rows),
        peptide_row_count=len(peptide_rows),
        protein_row_count=len(protein_rows),
        canonical_psm_count=len(canonical_psms),
        peptide_evidence_count=len(peptide_rows),
        protein_reference_count=len(protein_rows),
        open_search_evidence_count=len(open_search_evidence),
        protein_quantity_count=len(protein_quantity_rows),
        modified_psm_count=sum(1 for row in psm_rows if has_modified_content(row)),
        modified_peptide_row_count=sum(
            1 for row in peptide_rows if has_modified_content(row)
        ),
        open_search_psm_count=sum(1 for row in psm_rows if row.open_search_candidate),
        open_search_peptide_count=sum(
            1 for row in peptide_rows if row.open_search_candidate
        ),
        q_value_psm_count=sum(1 for row in psm_rows if row.q_value is not None),
        q_value_peptide_count=sum(1 for row in peptide_rows if row.q_value is not None),
        mapped_protein_count=len(protein_refs),
        target_protein_count=sum(
            1
            for row in protein_rows
            if row.target_decoy_label is TargetDecoyLabel.TARGET
        ),
        decoy_protein_count=sum(
            1
            for row in protein_rows
            if row.target_decoy_label is TargetDecoyLabel.DECOY
        ),
    )
    return FragpipeImportReport(
        psm_normalization=psm_normalization,
        canonical_psms=canonical_psms,
        psm_rows=psm_rows,
        peptide_evidence=peptide_rows,
        peptide_rows=peptide_rows,
        protein_references=protein_rows,
        protein_rows=protein_rows,
        open_search_evidence=open_search_evidence,
        protein_quantity_rows=protein_quantity_rows,
        rejected_evidence_rows=build_rejected_evidence_rows_from_psm_rows(
            psm_normalization.parse_report.rejected_rows,
            source_file=psm_tsv_path.name,
            entity_type="psm",
            entity_id_columns=("Spectrum", "Modified Peptide", "Peptide"),
        ),
        summary=summary,
    )
