# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Targeted panel design TSV loaders for Python interface entrypoints."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.identification.peptide_evidence import PeptideEvidenceClass
from bijux_proteomics.sequences import (
    PeptideChemicalLiabilityTier,
    PeptideDetectabilityTier,
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.assay_interference import (
    TargetedAssayInterferenceReason,
    TargetedAssayInterferenceRiskTier,
)
from bijux_proteomics.targeted.panel_design import (
    TargetedPanelAssayInput,
    TargetedPanelSelectedPeptideInput,
    TargetedPanelTransitionInput,
)

from ..targeted_selection_io.field_parsing import (
    _parse_cli_bool,
    _split_semicolon_field,
)


def _load_targeted_panel_selected_peptides(
    path: Path,
) -> tuple[TargetedPanelSelectedPeptideInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "selected-peptide TSV must include a header row for targeted panel building"
            )
        required_columns = {
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "rank",
            "observed_in_discovery",
            "observed_psm_count",
            "run_count",
            "detection_frequency",
            "replicate_consistency",
            "primary_evidence_class",
            "uniqueness_class",
            "uniqueness_score",
            "detectability_score",
            "detectability_tier",
            "suitability_score",
            "liability_tier",
            "liability_codes",
            "selection_score",
            "selection_reasons",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "selected-peptide TSV is missing required columns for targeted panel building: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedPanelSelectedPeptideInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                primary_class_raw = str(row.get("primary_evidence_class", "")).strip()
                rows.append(
                    TargetedPanelSelectedPeptideInput(
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            None
                            if not str(row.get("gene_symbol", "")).strip()
                            else str(row.get("gene_symbol", "")).strip()
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        rank=int(str(row.get("rank", "")).strip()),
                        observed_in_discovery=_parse_cli_bool(
                            row.get("observed_in_discovery", ""),
                            field_name="observed_in_discovery",
                        ),
                        observed_psm_count=(
                            None
                            if not str(row.get("observed_psm_count", "")).strip()
                            else int(str(row.get("observed_psm_count", "")).strip())
                        ),
                        run_count=(
                            None
                            if not str(row.get("run_count", "")).strip()
                            else int(str(row.get("run_count", "")).strip())
                        ),
                        detection_frequency=(
                            None
                            if not str(row.get("detection_frequency", "")).strip()
                            else float(str(row.get("detection_frequency", "")).strip())
                        ),
                        replicate_consistency=(
                            None
                            if not str(row.get("replicate_consistency", "")).strip()
                            else float(
                                str(row.get("replicate_consistency", "")).strip()
                            )
                        ),
                        primary_evidence_class=(
                            None
                            if not primary_class_raw
                            else PeptideEvidenceClass(primary_class_raw)
                        ),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        uniqueness_score=float(
                            str(row.get("uniqueness_score", "")).strip()
                        ),
                        detectability_score=float(
                            str(row.get("detectability_score", "")).strip()
                        ),
                        detectability_tier=PeptideDetectabilityTier(
                            str(row.get("detectability_tier", "")).strip()
                        ),
                        suitability_score=float(
                            str(row.get("suitability_score", "")).strip()
                        ),
                        liability_tier=PeptideChemicalLiabilityTier(
                            str(row.get("liability_tier", "")).strip()
                        ),
                        liability_codes=_split_semicolon_field(
                            row.get("liability_codes", "")
                        ),
                        selection_score=float(
                            str(row.get("selection_score", "")).strip()
                        ),
                        selection_reasons=_split_semicolon_field(
                            row.get("selection_reasons", "")
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid selected-peptide row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


def _load_targeted_panel_assay_inputs(
    path: Path,
) -> tuple[TargetedPanelAssayInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "assay-interference assay TSV must include a header row for targeted panel building"
            )
        required_columns = {
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "peptide_rank",
            "precursor_charge",
            "precursor_mz",
            "selected_transition_count",
            "exported_transition_count",
            "interference_risk_score",
            "interference_risk_tier",
            "downgrade_reasons",
            "panel_export_allowed",
            "panel_export_caveat",
            "source_library_entry_id",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "assay-interference assay TSV is missing required columns for targeted panel building: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedPanelAssayInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                downgrade_reasons = tuple(
                    TargetedAssayInterferenceReason(reason)
                    for reason in _split_semicolon_field(
                        row.get("downgrade_reasons", "")
                    )
                )
                rows.append(
                    TargetedPanelAssayInput(
                        assay_entry_id=str(row.get("assay_entry_id", "")).strip(),
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            None
                            if not str(row.get("gene_symbol", "")).strip()
                            else str(row.get("gene_symbol", "")).strip()
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        peptide_rank=int(str(row.get("peptide_rank", "")).strip()),
                        precursor_charge=int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        precursor_mz=float(str(row.get("precursor_mz", "")).strip()),
                        selected_transition_count=int(
                            str(row.get("selected_transition_count", "")).strip()
                        ),
                        exported_transition_count=int(
                            str(row.get("exported_transition_count", "")).strip()
                        ),
                        interference_risk_score=float(
                            str(row.get("interference_risk_score", "")).strip()
                        ),
                        interference_risk_tier=TargetedAssayInterferenceRiskTier(
                            str(row.get("interference_risk_tier", "")).strip()
                        ),
                        downgrade_reasons=downgrade_reasons,
                        panel_export_allowed=_parse_cli_bool(
                            row.get("panel_export_allowed", ""),
                            field_name="panel_export_allowed",
                        ),
                        panel_export_caveat=str(
                            row.get("panel_export_caveat", "")
                        ).strip(),
                        source_library_entry_id=(
                            None
                            if not str(row.get("source_library_entry_id", "")).strip()
                            else str(row.get("source_library_entry_id", "")).strip()
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid assay-interference assay row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


def _load_targeted_panel_transition_inputs(
    path: Path,
) -> tuple[TargetedPanelTransitionInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "assay-interference transition TSV must include a header row for targeted panel building"
            )
        required_columns = {
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "precursor_charge",
            "precursor_mz",
            "fragment_label",
            "ion_type",
            "fragment_ordinal",
            "fragment_charge",
            "fragment_sequence",
            "fragment_mz",
            "expected_relative_intensity",
            "selected_transition_rank",
            "interference_risk_score",
            "interference_risk_tier",
            "downgrade_reasons",
            "export_allowed",
            "export_caveat",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "assay-interference transition TSV is missing required columns for targeted panel building: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedPanelTransitionInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                downgrade_reasons = tuple(
                    TargetedAssayInterferenceReason(reason)
                    for reason in _split_semicolon_field(
                        row.get("downgrade_reasons", "")
                    )
                )
                rows.append(
                    TargetedPanelTransitionInput(
                        assay_entry_id=str(row.get("assay_entry_id", "")).strip(),
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            None
                            if not str(row.get("gene_symbol", "")).strip()
                            else str(row.get("gene_symbol", "")).strip()
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        precursor_charge=int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        precursor_mz=float(str(row.get("precursor_mz", "")).strip()),
                        fragment_label=str(row.get("fragment_label", "")).strip(),
                        ion_type=str(row.get("ion_type", "")).strip(),
                        fragment_ordinal=int(
                            str(row.get("fragment_ordinal", "")).strip()
                        ),
                        fragment_charge=int(
                            str(row.get("fragment_charge", "")).strip()
                        ),
                        fragment_sequence=str(row.get("fragment_sequence", "")).strip(),
                        fragment_mz=float(str(row.get("fragment_mz", "")).strip()),
                        expected_relative_intensity=(
                            None
                            if not str(
                                row.get("expected_relative_intensity", "")
                            ).strip()
                            else float(
                                str(row.get("expected_relative_intensity", "")).strip()
                            )
                        ),
                        selected_transition_rank=int(
                            str(row.get("selected_transition_rank", "")).strip()
                        ),
                        interference_risk_score=float(
                            str(row.get("interference_risk_score", "")).strip()
                        ),
                        interference_risk_tier=TargetedAssayInterferenceRiskTier(
                            str(row.get("interference_risk_tier", "")).strip()
                        ),
                        downgrade_reasons=downgrade_reasons,
                        export_allowed=_parse_cli_bool(
                            row.get("export_allowed", ""),
                            field_name="export_allowed",
                        ),
                        export_caveat=str(row.get("export_caveat", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid assay-interference transition row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = [
    "_load_targeted_panel_assay_inputs",
    "_load_targeted_panel_selected_peptides",
    "_load_targeted_panel_transition_inputs",
]
