# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Search-result and peptide-spectrum match contracts."""

from __future__ import annotations

from collections import defaultdict
import csv
from enum import StrEnum
import hashlib
import json
from pathlib import Path

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.chemistry import canonicalize_modified_peptide
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class TargetDecoyLabel(StrEnum):
    """Normalized target/decoy state for one evidence record."""

    TARGET = "target"
    DECOY = "decoy"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class PsmSortField(StrEnum):
    """Supported stable PSM sorting policies."""

    SPECTRUM = "spectrum"
    SCORE = "score"
    Q_VALUE = "q_value"
    PEPTIDE = "peptide"


class SearchResultColumnMapping(JsonModel):
    """User-supplied mapping from engine columns to the stable PSM contract."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    charge: str = Field(..., min_length=1)
    score: str = Field(..., min_length=1)
    protein_refs: str | None = None
    q_value: str | None = None
    decoy_label: str | None = None
    protein_separator: str = ";"


class TargetDecoyLabelPolicy(JsonModel):
    """Policy for inferring target-decoy labels from search-result fields."""

    model_config = ConfigDict(extra="forbid")

    protein_prefix: str | None = "DECOY_"
    protein_suffix: str | None = None
    explicit_decoy_values: tuple[str, ...] = ("decoy", "true", "1")
    explicit_target_values: tuple[str, ...] = ("target", "false", "0")

    @field_validator("explicit_decoy_values", "explicit_target_values", mode="before")
    @classmethod
    def _normalize_values(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            values = (value,)
        else:
            values = tuple(str(token) for token in value)
        return tuple(token.strip().lower() for token in values if token.strip())


class PsmRecord(JsonModel):
    """Stable peptide-spectrum match record."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN

    @field_validator("spectrum_id", "peptide", "canonical_peptide", mode="before")
    @classmethod
    def _strip_required_text(cls, value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError("field must not be blank")
        return text

    @field_validator("protein_refs", mode="before")
    @classmethod
    def _normalize_protein_refs(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            refs = [value]
        else:
            refs = [str(token) for token in value]
        normalized = tuple(token.strip() for token in refs if token.strip())
        return tuple(dict.fromkeys(normalized))


class SearchResultValidationIssue(JsonModel):
    """One validation issue while parsing or normalizing search results."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=1)


class RejectedPsmRow(JsonModel):
    """One rejected raw PSM row plus stable issue details."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[SearchResultValidationIssue, ...] = Field(default_factory=tuple)


class PsmParseReport(JsonModel):
    """Result of parsing one generic PSM TSV file."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPsmRow, ...] = Field(default_factory=tuple)
    column_mapping: SearchResultColumnMapping


class PeptideEvidenceEntry(JsonModel):
    """Rolled-up peptide-level evidence across PSMs."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    psm_count: int = Field(..., ge=1)
    spectrum_count: int = Field(..., ge=1)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN


class ProteinEvidenceEntry(JsonModel):
    """Rolled-up protein-level evidence across peptides and PSMs."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=1)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN


class FdrPolicy(JsonModel):
    """Stable policy for basic target-decoy FDR evaluation."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(default="higher_better", pattern="^(higher_better|lower_better)$")
    threshold: float | None = Field(default=None, ge=0.0)
    decoy_policy: TargetDecoyLabelPolicy = Field(default_factory=TargetDecoyLabelPolicy)


class FdrAnnotatedPsm(JsonModel):
    """PSM record plus cumulative target-decoy FDR state."""

    model_config = ConfigDict(extra="forbid")

    psm: PsmRecord
    rank: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool = True


class PsmSummaryReport(JsonModel):
    """Compact search-result summary over normalized PSM records."""

    model_config = ConfigDict(extra="forbid")

    total_psms: int = Field(..., ge=0)
    target_psms: int = Field(..., ge=0)
    decoy_psms: int = Field(..., ge=0)
    mixed_psms: int = Field(..., ge=0)
    unknown_psms: int = Field(..., ge=0)
    counts_by_charge: dict[str, int] = Field(default_factory=dict)
    counts_by_score_bin: dict[str, int] = Field(default_factory=dict)


class PeptideSummaryReport(JsonModel):
    """Compact peptide-level summary derived from PSM records."""

    model_config = ConfigDict(extra="forbid")

    total_peptides: int = Field(..., ge=0)
    modified_peptides: int = Field(..., ge=0)
    unique_peptides: int = Field(..., ge=0)
    shared_peptides: int = Field(..., ge=0)
    decoy_peptides: int = Field(..., ge=0)


class ProteinSummaryEntry(JsonModel):
    """One protein summary row with optional sequence coverage."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)


class ProteinSummaryReport(JsonModel):
    """Compact protein-level summary over evidence rollups."""

    model_config = ConfigDict(extra="forbid")

    total_proteins: int = Field(..., ge=0)
    target_proteins: int = Field(..., ge=0)
    decoy_proteins: int = Field(..., ge=0)
    protein_groups: tuple[ProteinSummaryEntry, ...] = Field(default_factory=tuple)


class SearchResultProvenanceManifest(JsonModel):
    """Stable manifest for one search-result parsing and filtering operation."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    source_path: str | None = None
    source_sha256: str | None = None
    total_rows: int = Field(..., ge=0)
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    column_mapping: SearchResultColumnMapping
    decoy_policy: TargetDecoyLabelPolicy
    fdr_policy: FdrPolicy | None = None


def _parse_protein_refs(raw_value: str | None, separator: str) -> tuple[str, ...]:
    if raw_value in (None, ""):
        return ()
    refs = tuple(token.strip() for token in raw_value.split(separator) if token.strip())
    return tuple(dict.fromkeys(refs))


def _rank_label(label: TargetDecoyLabel) -> int:
    if label is TargetDecoyLabel.DECOY:
        return 3
    if label is TargetDecoyLabel.MIXED:
        return 2
    if label is TargetDecoyLabel.TARGET:
        return 1
    return 0


def _combine_labels(labels: tuple[TargetDecoyLabel, ...]) -> TargetDecoyLabel:
    active = tuple(label for label in labels if label is not TargetDecoyLabel.UNKNOWN)
    if not active:
        return TargetDecoyLabel.UNKNOWN
    if all(label is TargetDecoyLabel.DECOY for label in active):
        return TargetDecoyLabel.DECOY
    if all(label is TargetDecoyLabel.TARGET for label in active):
        return TargetDecoyLabel.TARGET
    if any(label is TargetDecoyLabel.MIXED for label in active):
        return TargetDecoyLabel.MIXED
    return TargetDecoyLabel.MIXED


def parse_target_decoy_label(
    *,
    protein_refs: tuple[str, ...] = (),
    explicit_label: str | None = None,
    policy: TargetDecoyLabelPolicy | None = None,
) -> TargetDecoyLabel:
    """Parse target-decoy state from explicit and protein-reference signals."""
    active_policy = policy or TargetDecoyLabelPolicy()
    if explicit_label is not None and explicit_label.strip():
        normalized = explicit_label.strip().lower()
        if normalized in active_policy.explicit_decoy_values:
            return TargetDecoyLabel.DECOY
        if normalized in active_policy.explicit_target_values:
            return TargetDecoyLabel.TARGET

    if not protein_refs:
        return TargetDecoyLabel.UNKNOWN

    labels: list[TargetDecoyLabel] = []
    for protein_ref in protein_refs:
        is_prefix = (
            bool(active_policy.protein_prefix)
            and protein_ref.startswith(active_policy.protein_prefix)
        )
        is_suffix = (
            bool(active_policy.protein_suffix)
            and protein_ref.endswith(active_policy.protein_suffix)
        )
        labels.append(
            TargetDecoyLabel.DECOY if is_prefix or is_suffix else TargetDecoyLabel.TARGET
        )
    return _combine_labels(tuple(labels))


def _row_issue(code: str, message: str, row_number: int) -> SearchResultValidationIssue:
    return SearchResultValidationIssue(code=code, message=message, row_number=row_number)


def _parse_psm_row(
    row: dict[str, str],
    *,
    row_number: int,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy,
) -> PsmRecord:
    issues: list[SearchResultValidationIssue] = []

    spectrum_id = row.get(mapping.spectrum_id, "").strip()
    if not spectrum_id:
        issues.append(_row_issue("missing_spectrum_id", "missing spectrum identifier", row_number))

    peptide = row.get(mapping.peptide, "").strip()
    if not peptide:
        issues.append(_row_issue("missing_peptide", "missing peptide sequence", row_number))

    try:
        charge = int(row.get(mapping.charge, "").strip())
        if charge < 1:
            raise ValueError
    except ValueError:
        issues.append(_row_issue("invalid_charge", "invalid charge value", row_number))
        charge = 0

    try:
        score = float(row.get(mapping.score, "").strip())
    except ValueError:
        issues.append(_row_issue("invalid_score", "invalid score value", row_number))
        score = 0.0

    q_value: float | None = None
    if mapping.q_value:
        q_token = row.get(mapping.q_value, "").strip()
        if q_token:
            try:
                q_value = float(q_token)
                if q_value < 0:
                    raise ValueError
            except ValueError:
                issues.append(_row_issue("invalid_q_value", "invalid q-value", row_number))

    protein_refs = _parse_protein_refs(row.get(mapping.protein_refs) if mapping.protein_refs else None, mapping.protein_separator)
    explicit_label = row.get(mapping.decoy_label) if mapping.decoy_label else None

    canonical_peptide = peptide
    if peptide:
        try:
            canonical_peptide = canonicalize_modified_peptide(peptide)
        except ValueError as exc:
            issues.append(_row_issue("invalid_peptide_notation", str(exc), row_number))

    if issues:
        raise ValueError(RejectedPsmRow(row_number=row_number, raw_fields=row, issues=tuple(issues)).to_stable_json())

    return PsmRecord(
        spectrum_id=spectrum_id,
        peptide=peptide,
        canonical_peptide=canonical_peptide,
        charge=charge,
        score=score,
        q_value=q_value,
        protein_refs=protein_refs,
        target_decoy_label=parse_target_decoy_label(
            protein_refs=protein_refs,
            explicit_label=explicit_label,
            policy=decoy_policy,
        ),
    )


def parse_psm_tsv(
    path: Path,
    *,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> PsmParseReport:
    """Parse a generic peptide-spectrum match TSV into stable records."""
    active_policy = decoy_policy or TargetDecoyLabelPolicy()
    accepted_records: list[PsmRecord] = []
    rejected_rows: list[RejectedPsmRow] = []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("PSM TSV must include a header row")
        for required_column in (
            mapping.spectrum_id,
            mapping.peptide,
            mapping.charge,
            mapping.score,
        ):
            if required_column not in reader.fieldnames:
                raise ValueError(f"missing required PSM column {required_column!r}")

        for index, row in enumerate(reader, start=2):
            normalized_row = {str(key): str(value) for key, value in row.items() if key is not None}
            try:
                accepted_records.append(
                    _parse_psm_row(
                        normalized_row,
                        row_number=index,
                        mapping=mapping,
                        decoy_policy=active_policy,
                    )
                )
            except ValueError as exc:
                rejected_rows.append(RejectedPsmRow.model_validate_json(str(exc)))

    return PsmParseReport(
        total_rows=len(accepted_records) + len(rejected_rows),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=mapping,
    )


def normalize_psm_records(records: tuple[PsmRecord, ...]) -> tuple[PsmRecord, ...]:
    """Return a stable normalized PSM ordering for downstream exports."""
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.spectrum_id,
                record.q_value if record.q_value is not None else float("inf"),
                -record.score,
                record.canonical_peptide,
                record.charge,
            ),
        )
    )


def export_psm_jsonl(records: tuple[PsmRecord, ...], path: Path) -> None:
    """Write normalized PSM records as stable JSONL."""
    normalized = normalize_psm_records(records)
    with path.open("w", encoding="utf-8") as handle:
        for record in normalized:
            handle.write(json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def export_psm_tsv(records: tuple[PsmRecord, ...], path: Path) -> None:
    """Write normalized PSM records as a stable TSV table."""
    normalized = normalize_psm_records(records)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "spectrum_id",
                "peptide",
                "canonical_peptide",
                "charge",
                "score",
                "q_value",
                "protein_refs",
                "target_decoy_label",
            ]
        )
        for record in normalized:
            writer.writerow(
                [
                    record.spectrum_id,
                    record.peptide,
                    record.canonical_peptide,
                    record.charge,
                    record.score,
                    "" if record.q_value is None else record.q_value,
                    ";".join(record.protein_refs),
                    record.target_decoy_label.value,
                ]
            )


def sort_psm_records(
    records: tuple[PsmRecord, ...],
    *,
    by: PsmSortField = PsmSortField.SPECTRUM,
) -> tuple[PsmRecord, ...]:
    """Sort PSMs by one stable policy."""
    if by is PsmSortField.SPECTRUM:
        return tuple(sorted(records, key=lambda record: (record.spectrum_id, -record.score, record.canonical_peptide)))
    if by is PsmSortField.SCORE:
        return tuple(sorted(records, key=lambda record: (-record.score, record.spectrum_id, record.canonical_peptide)))
    if by is PsmSortField.Q_VALUE:
        return tuple(sorted(records, key=lambda record: (record.q_value if record.q_value is not None else float("inf"), record.spectrum_id, -record.score, record.canonical_peptide)))
    return tuple(sorted(records, key=lambda record: (record.canonical_peptide, record.spectrum_id, -record.score)))


def select_best_psm_per_spectrum(records: tuple[PsmRecord, ...]) -> tuple[PsmRecord, ...]:
    """Select one best PSM per spectrum with stable tie-breaking."""
    best_by_spectrum: dict[str, PsmRecord] = {}
    for record in records:
        current = best_by_spectrum.get(record.spectrum_id)
        if current is None:
            best_by_spectrum[record.spectrum_id] = record
            continue
        replacement_key = (
            record.score,
            -(record.q_value if record.q_value is not None else float("inf")),
            -_rank_label(record.target_decoy_label),
            record.canonical_peptide,
        )
        current_key = (
            current.score,
            -(current.q_value if current.q_value is not None else float("inf")),
            -_rank_label(current.target_decoy_label),
            current.canonical_peptide,
        )
        if replacement_key > current_key:
            best_by_spectrum[record.spectrum_id] = record
    return tuple(best_by_spectrum[key] for key in sorted(best_by_spectrum))


def rollup_peptide_evidence(records: tuple[PsmRecord, ...]) -> tuple[PeptideEvidenceEntry, ...]:
    """Roll up multiple PSMs into peptide-level evidence rows."""
    grouped: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        grouped[record.canonical_peptide].append(record)

    rollups: list[PeptideEvidenceEntry] = []
    for canonical_peptide in sorted(grouped):
        group = grouped[canonical_peptide]
        best = max(
            group,
            key=lambda record: (
                record.score,
                -(record.q_value if record.q_value is not None else float("inf")),
                record.peptide,
            ),
        )
        protein_refs = tuple(
            sorted(
                {
                    protein_ref
                    for record in group
                    for protein_ref in record.protein_refs
                }
            )
        )
        charge_states = tuple(sorted({record.charge for record in group}))
        spectra = {record.spectrum_id for record in group}
        q_values = [record.q_value for record in group if record.q_value is not None]
        rollups.append(
            PeptideEvidenceEntry(
                peptide=best.peptide,
                canonical_peptide=canonical_peptide,
                psm_count=len(group),
                spectrum_count=len(spectra),
                best_score=best.score,
                best_q_value=min(q_values) if q_values else None,
                charge_states=charge_states,
                protein_refs=protein_refs,
                target_decoy_label=_combine_labels(tuple(record.target_decoy_label for record in group)),
            )
        )
    return tuple(rollups)


def rollup_protein_evidence(records: tuple[PsmRecord, ...]) -> tuple[ProteinEvidenceEntry, ...]:
    """Roll up PSMs and peptides into protein-level evidence rows."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_to_peptides: dict[str, list[PeptideEvidenceEntry]] = defaultdict(list)
    protein_to_spectra: dict[str, set[str]] = defaultdict(set)

    record_by_peptide: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        record_by_peptide[record.canonical_peptide].append(record)

    for peptide_rollup in peptide_rollups:
        for protein_ref in peptide_rollup.protein_refs:
            protein_to_peptides[protein_ref].append(peptide_rollup)
            for record in record_by_peptide[peptide_rollup.canonical_peptide]:
                if protein_ref in record.protein_refs:
                    protein_to_spectra[protein_ref].add(record.spectrum_id)

    rollups: list[ProteinEvidenceEntry] = []
    for protein_ref in sorted(protein_to_peptides):
        peptides = protein_to_peptides[protein_ref]
        peptide_names = tuple(sorted(peptide.canonical_peptide for peptide in peptides))
        unique_peptide_count = sum(1 for peptide in peptides if len(peptide.protein_refs) == 1)
        shared_peptide_count = sum(1 for peptide in peptides if len(peptide.protein_refs) > 1)
        q_values = [peptide.best_q_value for peptide in peptides if peptide.best_q_value is not None]
        rollups.append(
            ProteinEvidenceEntry(
                protein_ref=protein_ref,
                peptide_count=len(peptides),
                unique_peptide_count=unique_peptide_count,
                shared_peptide_count=shared_peptide_count,
                best_score=max(peptide.best_score for peptide in peptides),
                best_q_value=min(q_values) if q_values else None,
                peptides=peptide_names,
                spectrum_count=len(protein_to_spectra[protein_ref]),
                target_decoy_label=parse_target_decoy_label(
                    protein_refs=(protein_ref,),
                ),
            )
        )
    return tuple(rollups)


def calculate_basic_target_decoy_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> tuple[FdrAnnotatedPsm, ...]:
    """Annotate PSMs with cumulative target-decoy FDR and monotonic q-values."""
    if score_orientation not in {"higher_better", "lower_better"}:
        raise ValueError("score_orientation must be 'higher_better' or 'lower_better'")

    sorted_records = tuple(
        sorted(
            records,
            key=(
                (lambda record: (-record.score, record.spectrum_id, record.canonical_peptide))
                if score_orientation == "higher_better"
                else (lambda record: (record.score, record.spectrum_id, record.canonical_peptide))
            ),
        )
    )
    annotated: list[FdrAnnotatedPsm] = []
    cumulative_targets = 0
    cumulative_decoys = 0
    for rank, record in enumerate(sorted_records, start=1):
        if record.target_decoy_label is TargetDecoyLabel.DECOY:
            cumulative_decoys += 1
        else:
            cumulative_targets += 1
        fdr = cumulative_decoys / max(cumulative_targets, 1)
        annotated.append(
            FdrAnnotatedPsm(
                psm=record,
                rank=rank,
                cumulative_targets=cumulative_targets,
                cumulative_decoys=cumulative_decoys,
                fdr=fdr,
                q_value=fdr,
                accepted=threshold is None or fdr <= threshold,
            )
        )

    running_min = float("inf")
    revised: list[FdrAnnotatedPsm] = []
    for entry in reversed(annotated):
        running_min = min(running_min, entry.fdr)
        revised.append(
            entry.model_copy(
                update={
                    "q_value": running_min,
                    "accepted": threshold is None or running_min <= threshold,
                }
            )
        )
    return tuple(reversed(revised))


def apply_q_values(records: tuple[PsmRecord, ...]) -> tuple[PsmRecord, ...]:
    """Return PSM records with q-values filled from target-decoy FDR."""
    annotated = calculate_basic_target_decoy_fdr(records)
    return tuple(
        entry.psm.model_copy(update={"q_value": entry.q_value})
        for entry in annotated
    )


def filter_psms_by_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float,
) -> tuple[PsmRecord, ...]:
    """Filter PSMs to those that pass the requested q-value threshold."""
    annotated = calculate_basic_target_decoy_fdr(records, threshold=threshold)
    return tuple(entry.psm.model_copy(update={"q_value": entry.q_value}) for entry in annotated if entry.accepted)


def build_psm_summary_report(
    records: tuple[PsmRecord, ...],
    *,
    score_bin_size: float = 10.0,
) -> PsmSummaryReport:
    """Build a compact summary report over normalized PSM records."""
    counts_by_charge: dict[str, int] = defaultdict(int)
    counts_by_score_bin: dict[str, int] = defaultdict(int)
    target_psms = 0
    decoy_psms = 0
    mixed_psms = 0
    unknown_psms = 0
    for record in records:
        counts_by_charge[str(record.charge)] += 1
        lower = int(record.score // score_bin_size) * int(score_bin_size)
        upper = lower + int(score_bin_size)
        counts_by_score_bin[f"{lower}-{upper}"] += 1
        if record.target_decoy_label is TargetDecoyLabel.TARGET:
            target_psms += 1
        elif record.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_psms += 1
        elif record.target_decoy_label is TargetDecoyLabel.MIXED:
            mixed_psms += 1
        else:
            unknown_psms += 1
    return PsmSummaryReport(
        total_psms=len(records),
        target_psms=target_psms,
        decoy_psms=decoy_psms,
        mixed_psms=mixed_psms,
        unknown_psms=unknown_psms,
        counts_by_charge=dict(sorted(counts_by_charge.items())),
        counts_by_score_bin=dict(sorted(counts_by_score_bin.items())),
    )


def build_peptide_summary_report(records: tuple[PsmRecord, ...]) -> PeptideSummaryReport:
    """Build a compact peptide-level summary report."""
    peptide_rollups = rollup_peptide_evidence(records)
    return PeptideSummaryReport(
        total_peptides=len(peptide_rollups),
        modified_peptides=sum(1 for peptide in peptide_rollups if "[" in peptide.canonical_peptide),
        unique_peptides=sum(1 for peptide in peptide_rollups if len(peptide.protein_refs) == 1),
        shared_peptides=sum(1 for peptide in peptide_rollups if len(peptide.protein_refs) > 1),
        decoy_peptides=sum(1 for peptide in peptide_rollups if peptide.target_decoy_label is TargetDecoyLabel.DECOY),
    )


def build_protein_summary_report(
    records: tuple[PsmRecord, ...],
    *,
    protein_lengths: dict[str, int] | None = None,
) -> ProteinSummaryReport:
    """Build a compact protein-level summary report with optional coverage."""
    rollups = rollup_protein_evidence(records)
    summary_entries: list[ProteinSummaryEntry] = []
    target_proteins = 0
    decoy_proteins = 0
    for rollup in rollups:
        coverage_fraction: float | None = None
        if protein_lengths and protein_lengths.get(rollup.protein_ref):
            covered_residues = {
                residue_index
                for peptide in rollup.peptides
                for residue_index in range(1, len(peptide) + 1)
            }
            coverage_fraction = min(
                len(covered_residues) / protein_lengths[rollup.protein_ref],
                1.0,
            )
        summary_entries.append(
            ProteinSummaryEntry(
                protein_ref=rollup.protein_ref,
                peptide_count=rollup.peptide_count,
                unique_peptide_count=rollup.unique_peptide_count,
                shared_peptide_count=rollup.shared_peptide_count,
                coverage_fraction=coverage_fraction,
            )
        )
        if rollup.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_proteins += 1
        else:
            target_proteins += 1
    return ProteinSummaryReport(
        total_proteins=len(summary_entries),
        target_proteins=target_proteins,
        decoy_proteins=decoy_proteins,
        protein_groups=tuple(summary_entries),
    )


def build_search_result_provenance_manifest(
    *,
    source_path: Path,
    parse_report: PsmParseReport,
    decoy_policy: TargetDecoyLabelPolicy,
    fdr_policy: FdrPolicy | None = None,
) -> SearchResultProvenanceManifest:
    """Build a stable provenance manifest for one parsed search-result table."""
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_result_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchResultProvenanceManifest(
        document_schema=schema,
        source_path=str(source_path),
        source_sha256=source_sha256,
        total_rows=parse_report.total_rows,
        accepted_rows=len(parse_report.accepted_records),
        rejected_rows=len(parse_report.rejected_rows),
        column_mapping=parse_report.column_mapping,
        decoy_policy=decoy_policy,
        fdr_policy=fdr_policy,
    )
    payload = manifest.to_dict()
    return manifest.model_copy(
        update={"document_schema": manifest.document_schema.with_content_hash(payload)}
    )
