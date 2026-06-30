# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""OpenMS import over practical idXML and exported feature-table evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from defusedxml import ElementTree as ET
from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
    build_rejected_evidence_rows_from_scientific_rows,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.quantification.contracts import (
        Ms1FeatureParseReport,
        Ms1FeatureRecord,
    )


class OpenMsPsmReviewEntry(JsonModel):
    """Reviewer-facing PSM row from one OpenMS idXML import."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    spectrum_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    mz: float | None = Field(default=None, gt=0.0)
    retention_time_seconds: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    provenance: ImportedEvidenceProvenance


class OpenMsProteinReviewEntry(JsonModel):
    """Reviewer-facing protein-evidence row from one OpenMS idXML import."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    score: float | None = None
    q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel
    provenance: ImportedEvidenceProvenance


class OpenMsFeatureReviewEntry(JsonModel):
    """Reviewer-facing exported feature row from one OpenMS feature table."""

    model_config = ConfigDict(extra="forbid")

    feature_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    intensity: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    charge: int | None = Field(default=None, ge=1)
    mz: float | None = Field(default=None, gt=0.0)
    retention_time_seconds: float | None = Field(default=None, ge=0.0)
    missing_reason: str | None = None
    provenance: ImportedEvidenceProvenance


class OpenMsFeatureValidationIssue(JsonModel):
    """One stable issue carried from the OpenMS feature-table parser."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class OpenMsRejectedFeatureRow(JsonModel):
    """One rejected OpenMS feature-table row with stable issue details."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[OpenMsFeatureValidationIssue, ...] = Field(default_factory=tuple)


class OpenMsImportSummary(JsonModel):
    """Compact summary over one OpenMS import bundle."""

    model_config = ConfigDict(extra="forbid")

    accepted_psm_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    accepted_feature_count: int = Field(..., ge=0)
    rejected_feature_count: int = Field(..., ge=0)
    q_value_psm_count: int = Field(..., ge=0)
    q_value_protein_count: int = Field(..., ge=0)
    target_psm_count: int = Field(..., ge=0)
    decoy_psm_count: int = Field(..., ge=0)
    target_protein_count: int = Field(..., ge=0)
    decoy_protein_count: int = Field(..., ge=0)
    feature_sample_count: int = Field(..., ge=0)
    feature_samples: tuple[str, ...] = Field(default_factory=tuple)


class OpenMsFeatureParseSummary(JsonModel):
    """Accepted-versus-rejected counts from the exported feature-table parse."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)


class OpenMsImportReport(JsonModel):
    """One governed OpenMS import report over idXML and feature-table evidence."""

    model_config = ConfigDict(extra="forbid")

    psm_rows: tuple[OpenMsPsmReviewEntry, ...] = Field(default_factory=tuple)
    protein_rows: tuple[OpenMsProteinReviewEntry, ...] = Field(default_factory=tuple)
    feature_rows: tuple[OpenMsFeatureReviewEntry, ...] = Field(default_factory=tuple)
    rejected_feature_rows: tuple[OpenMsRejectedFeatureRow, ...] = Field(
        default_factory=tuple
    )
    rejected_evidence_rows: tuple[RejectedEvidenceTableEntry, ...] = Field(
        default_factory=tuple
    )
    feature_parse_summary: OpenMsFeatureParseSummary
    summary: OpenMsImportSummary


def build_openms_import_report(
    idxml_path: Path,
    *,
    feature_table_path: Path,
) -> OpenMsImportReport:
    """Import one OpenMS identification bundle with practical exported features."""
    psm_rows, protein_rows = _parse_openms_idxml(idxml_path)
    feature_report = _parse_openms_feature_table(feature_table_path)
    feature_rows = tuple(
        _build_feature_review_entry(record)
        for record in feature_report.accepted_records
    )
    rejected_feature_rows = _build_rejected_feature_rows(feature_report)
    feature_samples = tuple(sorted({row.sample_id for row in feature_rows}))
    summary = OpenMsImportSummary(
        accepted_psm_count=len(psm_rows),
        protein_row_count=len(protein_rows),
        accepted_feature_count=len(feature_rows),
        rejected_feature_count=len(feature_report.rejected_rows),
        q_value_psm_count=sum(1 for row in psm_rows if row.q_value is not None),
        q_value_protein_count=sum(1 for row in protein_rows if row.q_value is not None),
        target_psm_count=sum(
            1 for row in psm_rows if row.target_decoy_label is TargetDecoyLabel.TARGET
        ),
        decoy_psm_count=sum(
            1 for row in psm_rows if row.target_decoy_label is TargetDecoyLabel.DECOY
        ),
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
        feature_sample_count=len(feature_samples),
        feature_samples=feature_samples,
    )
    return OpenMsImportReport(
        psm_rows=psm_rows,
        protein_rows=protein_rows,
        feature_rows=feature_rows,
        rejected_feature_rows=rejected_feature_rows,
        rejected_evidence_rows=build_rejected_evidence_rows_from_scientific_rows(
            feature_report.rejected_rows,
            source_file=feature_table_path.name,
            entity_type="ms1_feature",
            entity_id_columns=("feature_id", "sequence"),
        ),
        feature_parse_summary=OpenMsFeatureParseSummary(
            total_rows=feature_report.total_rows,
            accepted_rows=len(feature_report.accepted_records),
            rejected_rows=len(feature_report.rejected_rows),
        ),
        summary=summary,
    )


def render_openms_summary_tsv(summary: OpenMsImportSummary) -> str:
    """Render the one-row OpenMS summary as TSV."""
    header = (
        "accepted_psm_count",
        "protein_row_count",
        "accepted_feature_count",
        "rejected_feature_count",
        "q_value_psm_count",
        "q_value_protein_count",
        "target_psm_count",
        "decoy_psm_count",
        "target_protein_count",
        "decoy_protein_count",
        "feature_sample_count",
        "feature_samples",
    )
    row = (
        str(summary.accepted_psm_count),
        str(summary.protein_row_count),
        str(summary.accepted_feature_count),
        str(summary.rejected_feature_count),
        str(summary.q_value_psm_count),
        str(summary.q_value_protein_count),
        str(summary.target_psm_count),
        str(summary.decoy_psm_count),
        str(summary.target_protein_count),
        str(summary.decoy_protein_count),
        str(summary.feature_sample_count),
        ";".join(summary.feature_samples),
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_openms_psm_tsv(rows: tuple[OpenMsPsmReviewEntry, ...]) -> str:
    """Render reviewer-facing OpenMS PSM rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "run_id",
        "spectrum_id",
        "charge",
        "peptide_sequence",
    )
    lines = [
        "\t".join(
            (
                "run_id",
                "spectrum_id",
                "peptide_sequence",
                "charge",
                "score",
                "q_value",
                "mz",
                "retention_time_seconds",
                "protein_refs",
                "target_decoy_label",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.run_id,
                    row.spectrum_id,
                    row.peptide_sequence,
                    str(row.charge),
                    f"{row.score:.6g}",
                    "" if row.q_value is None else f"{row.q_value:.6g}",
                    "" if row.mz is None else f"{row.mz:.6g}",
                    ""
                    if row.retention_time_seconds is None
                    else f"{row.retention_time_seconds:.6g}",
                    ";".join(sort_strings(row.protein_refs)),
                    row.target_decoy_label.value,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_openms_protein_tsv(rows: tuple[OpenMsProteinReviewEntry, ...]) -> str:
    """Render reviewer-facing OpenMS protein rows as TSV."""
    ordered_rows = sort_rows_by_fields(rows, "run_id", "protein_ref")
    lines = [
        "\t".join(
            (
                "run_id",
                "protein_ref",
                "score",
                "q_value",
                "target_decoy_label",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.run_id,
                    row.protein_ref,
                    "" if row.score is None else f"{row.score:.6g}",
                    "" if row.q_value is None else f"{row.q_value:.6g}",
                    row.target_decoy_label.value,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_openms_feature_tsv(rows: tuple[OpenMsFeatureReviewEntry, ...]) -> str:
    """Render reviewer-facing OpenMS feature rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "sample_id",
        "feature_id",
        "canonical_peptide",
    )
    lines = [
        "\t".join(
            (
                "feature_id",
                "sample_id",
                "peptide_sequence",
                "canonical_peptide",
                "intensity",
                "protein_refs",
                "charge",
                "mz",
                "retention_time_seconds",
                "missing_reason",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.feature_id,
                    row.sample_id,
                    row.peptide_sequence,
                    row.canonical_peptide,
                    "" if row.intensity is None else f"{row.intensity:.6g}",
                    ";".join(sort_strings(row.protein_refs)),
                    "" if row.charge is None else str(row.charge),
                    "" if row.mz is None else f"{row.mz:.6g}",
                    ""
                    if row.retention_time_seconds is None
                    else f"{row.retention_time_seconds:.6g}",
                    row.missing_reason or "",
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_openms_rejected_feature_tsv(
    rows: tuple[OpenMsRejectedFeatureRow, ...],
) -> str:
    """Render rejected OpenMS feature-table rows as TSV."""

    ordered_rows = tuple(sorted(rows, key=lambda row: row.row_number))
    lines = [
        "\t".join(
            (
                "row_number",
                "issue_codes",
                "issue_messages",
                "raw_fields_json",
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    str(row.row_number),
                    ";".join(issue.code for issue in row.issues),
                    ";".join(issue.message for issue in row.issues),
                    json.dumps(row.raw_fields, sort_keys=True, separators=(",", ":")),
                )
            )
        )
    return "\n".join(lines) + "\n"


def _parse_openms_idxml(
    idxml_path: Path,
) -> tuple[tuple[OpenMsPsmReviewEntry, ...], tuple[OpenMsProteinReviewEntry, ...]]:
    root = _parse_openms_idxml_root(idxml_path)
    if root is None:
        raise ValueError("invalid idXML: missing document root")
    if _local_name(root.tag) != "IdXML":
        raise ValueError("OpenMS import expects an idXML root document")

    protein_rows: list[OpenMsProteinReviewEntry] = []
    protein_run_ids: list[str] = []
    protein_row_number = 1
    for protein_identification in root.findall(".//{*}ProteinIdentification"):
        run_id = (
            protein_identification.attrib.get("id", "openms-run").strip()
            or "openms-run"
        )
        protein_run_ids.append(run_id)
        score_type = protein_identification.attrib.get("score_type", "")
        for protein_hit in protein_identification.findall("{*}ProteinHit"):
            accession = protein_hit.attrib.get("accession", "").strip()
            if not accession:
                continue
            score = _required_float(
                protein_hit.attrib.get("score"),
                context=f"protein hit {accession}",
            )
            protein_rows.append(
                OpenMsProteinReviewEntry(
                    run_id=run_id,
                    protein_ref=accession,
                    score=score,
                    q_value=_reported_q_value(
                        explicit_q_value=protein_hit.attrib.get("q_value"),
                        score=score,
                        score_type=score_type,
                    ),
                    target_decoy_label=_protein_label(accession),
                    provenance=ImportedEvidenceProvenance.from_single_row(
                        source_engine="openms-idxml",
                        source_file=str(idxml_path),
                        source_row_number=protein_row_number,
                        original_identifiers={
                            "run_id": run_id,
                            "protein_ref": accession,
                        },
                    ),
                )
            )
            protein_row_number += 1

    psm_rows: list[OpenMsPsmReviewEntry] = []
    default_run_id = (
        protein_run_ids[0] if len(set(protein_run_ids)) == 1 else "openms-run"
    )
    psm_row_number = 1
    for peptide_identification in root.findall(".//{*}PeptideIdentification"):
        run_id = (
            peptide_identification.attrib.get("protein_identification_ref")
            or peptide_identification.attrib.get("protein_ref")
            or default_run_id
        ).strip() or default_run_id
        spectrum_id = peptide_identification.attrib.get(
            "spectrum_reference", ""
        ).strip()
        rt = _optional_float(peptide_identification.attrib.get("RT"))
        mz = _optional_float(peptide_identification.attrib.get("MZ"))
        score_type = peptide_identification.attrib.get("score_type", "")
        for peptide_hit in peptide_identification.findall("{*}PeptideHit"):
            sequence = peptide_hit.attrib.get("sequence", "").strip()
            if not sequence:
                continue
            score = _required_float(
                peptide_hit.attrib.get("score"),
                context=f"peptide hit {sequence}",
            )
            evidence_accessions = tuple(
                sorted(
                    {
                        evidence.attrib.get("protein_ref", "").strip()
                        for evidence in peptide_hit.findall("{*}PeptideEvidence")
                        if evidence.attrib.get("protein_ref", "").strip()
                    }
                )
            )
            target_decoy_label = (
                TargetDecoyLabel.DECOY
                if evidence_accessions
                and all(ref.startswith("DECOY_") for ref in evidence_accessions)
                else TargetDecoyLabel.TARGET
            )
            psm_rows.append(
                OpenMsPsmReviewEntry(
                    run_id=run_id,
                    spectrum_id=spectrum_id or f"{run_id}:{sequence}",
                    peptide_sequence=sequence,
                    charge=_required_charge(
                        peptide_hit.attrib.get("charge"),
                        sequence=sequence,
                    ),
                    score=score,
                    q_value=_reported_q_value(
                        explicit_q_value=peptide_hit.attrib.get("q_value"),
                        score=score,
                        score_type=score_type,
                    ),
                    mz=mz,
                    retention_time_seconds=rt,
                    protein_refs=evidence_accessions,
                    target_decoy_label=target_decoy_label,
                    provenance=ImportedEvidenceProvenance.from_single_row(
                        source_engine="openms-idxml",
                        source_file=str(idxml_path),
                        source_row_number=psm_row_number,
                        original_identifiers={
                            "run_id": run_id,
                            "spectrum_id": spectrum_id or f"{run_id}:{sequence}",
                            "peptide_sequence": sequence,
                        },
                    ),
                )
            )
            psm_row_number += 1
    return (
        tuple(sorted(psm_rows, key=lambda row: (-row.score, row.spectrum_id))),
        tuple(sorted(protein_rows, key=lambda row: row.protein_ref)),
    )


def _parse_openms_feature_table(feature_table_path: Path) -> Ms1FeatureParseReport:
    from bijux_proteomics.quantification import (
        Ms1FeatureColumnMapping,
        parse_ms1_feature_table,
    )

    mapping = Ms1FeatureColumnMapping(
        sample_id="sample_id",
        peptide="sequence",
        intensity="intensity",
        protein_refs="protein_accessions",
        feature_id="feature_id",
        charge="charge",
        mz="mz",
        retention_time_seconds="rt_seconds",
        missing_reason="missing_reason",
    )
    return parse_ms1_feature_table(feature_table_path, mapping=mapping)


def _build_rejected_feature_rows(
    feature_report: Ms1FeatureParseReport,
) -> tuple[OpenMsRejectedFeatureRow, ...]:
    rows = [
        OpenMsRejectedFeatureRow(
            row_number=row.row_number,
            raw_fields=row.raw_fields,
            issues=tuple(
                OpenMsFeatureValidationIssue(
                    code=issue.code,
                    message=issue.message,
                    row_number=issue.row_number,
                )
                for issue in row.issues
            ),
        )
        for row in feature_report.rejected_rows
    ]
    return tuple(sorted(rows, key=lambda row: row.row_number))


def _build_feature_review_entry(record: Ms1FeatureRecord) -> OpenMsFeatureReviewEntry:
    return OpenMsFeatureReviewEntry(
        feature_id=record.feature_id,
        sample_id=record.sample_id,
        peptide_sequence=record.peptide,
        canonical_peptide=record.canonical_peptide,
        intensity=record.intensity,
        protein_refs=record.protein_refs,
        charge=record.charge,
        mz=record.mz,
        retention_time_seconds=record.retention_time_seconds,
        missing_reason=record.missing_reason,
        provenance=record.provenance,
    )


def _parse_openms_idxml_root(path: Path) -> Any:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        line_number, column_number = _parse_error_location(exc)
        if line_number is not None and column_number is not None:
            raise ValueError(
                "OpenMS idXML parse error in "
                f"{path.name} at line {line_number}, column {column_number}: {exc}"
            ) from exc
        raise ValueError(f"OpenMS idXML parse error in {path.name}: {exc}") from exc
    if root is None:
        raise ValueError("invalid idXML: missing document root")
    return root


def _parse_error_location(exc: ET.ParseError) -> tuple[int | None, int | None]:
    position = getattr(exc, "position", None)
    if (
        isinstance(position, tuple)
        and len(position) == 2
        and isinstance(position[0], int)
        and isinstance(position[1], int)
    ):
        return position
    return (None, None)


def _protein_label(accession: str) -> TargetDecoyLabel:
    return (
        TargetDecoyLabel.DECOY
        if accession.startswith("DECOY_")
        else TargetDecoyLabel.TARGET
    )


def _optional_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value.strip())


def _required_float(value: str | None, *, context: str) -> float:
    parsed = _optional_float(value)
    if parsed is None:
        raise ValueError(f"OpenMS import requires a numeric score for {context}")
    return parsed


def _required_charge(value: str | None, *, sequence: str) -> int:
    if value is None or not value.strip():
        raise ValueError(
            f"OpenMS import requires a positive peptide charge for {sequence}"
        )
    charge = int(value.strip())
    if charge < 1:
        raise ValueError(
            f"OpenMS import requires a positive peptide charge for {sequence}"
        )
    return charge


def _reported_q_value(
    *,
    explicit_q_value: str | None,
    score: float,
    score_type: str,
) -> float | None:
    reported = _optional_float(explicit_q_value)
    if reported is not None:
        return reported
    if _is_q_value_score_type(score_type):
        return score
    return None


def _is_q_value_score_type(score_type: str) -> bool:
    normalized = (
        score_type.strip().lower().replace("-", "").replace("_", "").replace(" ", "")
    )
    return normalized in {"qvalue"}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
