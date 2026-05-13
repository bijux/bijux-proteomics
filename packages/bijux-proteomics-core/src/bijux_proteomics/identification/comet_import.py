# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Comet result import over tabular and practical pepXML evidence."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
import xml.etree.ElementTree as ET

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.search_engine_modified_peptides import (
    SearchEngineModifiedPeptideDialect,
    build_search_engine_modified_peptide_report,
)
from bijux_proteomics_foundation import JsonModel

from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchParameterReport,
    normalize_search_results_with_adapter,
    parse_search_parameter_file,
)


class CometImportKind(StrEnum):
    """Supported Comet import sources."""

    TABULAR = "tabular"
    PEPXML = "pepxml"


class CometPsmReviewEntry(JsonModel):
    """Reviewer-facing Comet identification row."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    residue_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modification_count: int = Field(..., ge=0)
    charge: int = Field(..., ge=1)
    expectation_value: float = Field(..., ge=0.0)
    xcorr: float | None = None
    delta_cn: float | None = None
    sp_score: float | None = None
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel


class CometImportSummary(JsonModel):
    """Compact summary over imported Comet evidence."""

    model_config = ConfigDict(extra="forbid")

    accepted_psm_count: int = Field(..., ge=0)
    rejected_psm_count: int = Field(..., ge=0)
    modified_psm_count: int = Field(..., ge=0)
    xcorr_psm_count: int = Field(..., ge=0)
    delta_cn_psm_count: int = Field(..., ge=0)
    expectation_value_psm_count: int = Field(..., ge=0)
    multi_protein_psm_count: int = Field(..., ge=0)
    target_psm_count: int = Field(..., ge=0)
    decoy_psm_count: int = Field(..., ge=0)


class CometImportReport(JsonModel):
    """One governed Comet import report."""

    model_config = ConfigDict(extra="forbid")

    import_kind: CometImportKind
    normalization: SearchAdapterNormalizationReport | None = None
    psm_rows: tuple[CometPsmReviewEntry, ...] = Field(default_factory=tuple)
    summary: CometImportSummary
    parameter_report: SearchParameterReport | None = None


def build_comet_import_report(
    result_path: Path,
    *,
    config_path: Path | None = None,
) -> CometImportReport:
    """Import one Comet result file from tabular or practical pepXML evidence."""
    suffixes = {suffix.lower() for suffix in result_path.suffixes}
    parameter_report = (
        None
        if config_path is None
        else parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind.COMET,
        )
    )
    if ".pepxml" in suffixes or result_path.suffix.lower() == ".pepxml":
        psm_rows = _parse_comet_pepxml(result_path)
        summary = _build_summary(psm_rows, rejected_psm_count=0)
        return CometImportReport(
            import_kind=CometImportKind.PEPXML,
            psm_rows=psm_rows,
            summary=summary,
            parameter_report=parameter_report,
        )

    normalization = normalize_search_results_with_adapter(
        source_path=result_path,
        adapter_kind=SearchAdapterKind.COMET,
        dialect_id="comet-psm",
    )
    psm_rows = _build_tabular_rows(normalization)
    summary = _build_summary(
        psm_rows,
        rejected_psm_count=len(normalization.parse_report.rejected_rows),
    )
    return CometImportReport(
        import_kind=CometImportKind.TABULAR,
        normalization=normalization,
        psm_rows=psm_rows,
        summary=summary,
        parameter_report=parameter_report,
    )


def render_comet_summary_tsv(summary: CometImportSummary) -> str:
    """Render the one-row Comet summary as TSV."""
    header = (
        "accepted_psm_count",
        "rejected_psm_count",
        "modified_psm_count",
        "xcorr_psm_count",
        "delta_cn_psm_count",
        "expectation_value_psm_count",
        "multi_protein_psm_count",
        "target_psm_count",
        "decoy_psm_count",
    )
    row = (
        str(summary.accepted_psm_count),
        str(summary.rejected_psm_count),
        str(summary.modified_psm_count),
        str(summary.xcorr_psm_count),
        str(summary.delta_cn_psm_count),
        str(summary.expectation_value_psm_count),
        str(summary.multi_protein_psm_count),
        str(summary.target_psm_count),
        str(summary.decoy_psm_count),
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_comet_psm_tsv(rows: tuple[CometPsmReviewEntry, ...]) -> str:
    """Render reviewer-facing Comet rows as TSV."""
    lines = [
        "\t".join(
            (
                "spectrum_id",
                "peptide",
                "residue_sequence",
                "canonical_peptide",
                "modification_count",
                "charge",
                "expectation_value",
                "xcorr",
                "delta_cn",
                "sp_score",
                "protein_refs",
                "target_decoy_label",
            )
        )
    ]
    for row in rows:
        lines.append(
            "\t".join(
                (
                    row.spectrum_id,
                    row.peptide,
                    row.residue_sequence,
                    row.canonical_peptide,
                    str(row.modification_count),
                    str(row.charge),
                    f"{row.expectation_value:.6g}",
                    "" if row.xcorr is None else f"{row.xcorr:.6g}",
                    "" if row.delta_cn is None else f"{row.delta_cn:.6g}",
                    "" if row.sp_score is None else f"{row.sp_score:.6g}",
                    ";".join(row.protein_refs),
                    row.target_decoy_label.value,
                )
            )
        )
    return "\n".join(lines) + "\n"


def _build_summary(
    rows: tuple[CometPsmReviewEntry, ...],
    *,
    rejected_psm_count: int,
) -> CometImportSummary:
    return CometImportSummary(
        accepted_psm_count=len(rows),
        rejected_psm_count=rejected_psm_count,
        modified_psm_count=sum(1 for row in rows if row.modification_count > 0),
        xcorr_psm_count=sum(1 for row in rows if row.xcorr is not None),
        delta_cn_psm_count=sum(1 for row in rows if row.delta_cn is not None),
        expectation_value_psm_count=sum(1 for row in rows if row.expectation_value >= 0.0),
        multi_protein_psm_count=sum(1 for row in rows if len(row.protein_refs) > 1),
        target_psm_count=sum(
            1 for row in rows if row.target_decoy_label is TargetDecoyLabel.TARGET
        ),
        decoy_psm_count=sum(
            1 for row in rows if row.target_decoy_label is TargetDecoyLabel.DECOY
        ),
    )


def _build_tabular_rows(
    normalization: SearchAdapterNormalizationReport,
) -> tuple[CometPsmReviewEntry, ...]:
    rows: list[CometPsmReviewEntry] = []
    for evidence_row in normalization.evidence_rows:
        if not evidence_row.accepted or evidence_row.normalized_record is None:
            continue
        record = evidence_row.normalized_record
        raw = evidence_row.raw_fields
        peptide_report = build_search_engine_modified_peptide_report(
            raw.get("modified_peptide", record.peptide),
            dialect=SearchEngineModifiedPeptideDialect.COMET,
        )
        rows.append(
            CometPsmReviewEntry(
                spectrum_id=record.spectrum_id,
                peptide=raw.get("modified_peptide", record.peptide),
                residue_sequence=peptide_report.residue_sequence,
                canonical_peptide=record.canonical_peptide,
                modification_count=len(peptide_report.modifications),
                charge=record.charge,
                expectation_value=record.score,
                xcorr=_optional_float(raw.get("xcorr")),
                delta_cn=_optional_float(raw.get("delta_cn")),
                sp_score=_optional_float(raw.get("sp_score")),
                protein_refs=record.protein_refs,
                target_decoy_label=record.target_decoy_label,
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.expectation_value,
                -_sort_value(row.xcorr),
                row.spectrum_id,
            ),
        )
    )


def _parse_comet_pepxml(path: Path) -> tuple[CometPsmReviewEntry, ...]:
    root = ET.parse(path).getroot()
    rows: list[CometPsmReviewEntry] = []
    for query in root.findall(".//{*}spectrum_query"):
        spectrum_id = query.attrib.get("spectrum")
        assumed_charge = int(query.attrib["assumed_charge"])
        for result in query.findall("./{*}search_result/{*}search_hit"):
            peptide = result.attrib["peptide"]
            proteins = [result.attrib["protein"]]
            proteins.extend(
                alternative.attrib["protein"]
                for alternative in result.findall("./{*}alternative_protein")
                if alternative.attrib.get("protein")
            )
            modified_peptide = peptide
            modification_info = result.find("./{*}modification_info")
            if modification_info is not None:
                modified_peptide = modification_info.attrib.get(
                    "modified_peptide", peptide
                )
            peptide_report = build_search_engine_modified_peptide_report(
                modified_peptide,
                dialect=SearchEngineModifiedPeptideDialect.COMET,
            )
            score_map = {
                score.attrib.get("name"): score.attrib.get("value")
                for score in result.findall("./{*}search_score")
            }
            rows.append(
                CometPsmReviewEntry(
                    spectrum_id=spectrum_id or peptide,
                    peptide=modified_peptide,
                    residue_sequence=peptide_report.residue_sequence,
                    canonical_peptide=peptide_report.canonical_notation,
                    modification_count=len(peptide_report.modifications),
                    charge=assumed_charge,
                    expectation_value=float(score_map.get("expect", "0")),
                    xcorr=_optional_float(score_map.get("xcorr")),
                    delta_cn=_optional_float(score_map.get("deltacn")),
                    sp_score=_optional_float(score_map.get("spscore")),
                    protein_refs=tuple(dict.fromkeys(proteins)),
                    target_decoy_label=_label_from_proteins(tuple(proteins)),
                )
            )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.expectation_value,
                -_sort_value(row.xcorr),
                row.spectrum_id,
            ),
        )
    )


def _label_from_proteins(proteins: tuple[str, ...]) -> TargetDecoyLabel:
    if not proteins:
        return TargetDecoyLabel.UNKNOWN
    decoy = [protein for protein in proteins if protein.startswith("DECOY_")]
    if len(decoy) == len(proteins):
        return TargetDecoyLabel.DECOY
    if decoy:
        return TargetDecoyLabel.MIXED
    return TargetDecoyLabel.TARGET


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def _sort_value(value: float | None) -> float:
    return value if value is not None else float("-inf")
