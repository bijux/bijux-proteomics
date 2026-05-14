# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Study metadata and lab handoff surfaces."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class StudyMetadataRecord(JsonModel):
    """One normalized study metadata row connecting sample and run context."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    cohort_id: str = Field(..., min_length=1)
    condition_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    replicate_id: str = Field(..., min_length=1)
    fraction_id: str = Field(..., min_length=1)
    instrument_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    multiplex_channel: str | None = None
    spectra_file: str | None = None


class StudyMetadataModel(JsonModel):
    """Stable collection of normalized study metadata records."""

    model_config = ConfigDict(extra="forbid")

    records: tuple[StudyMetadataRecord, ...] = Field(default_factory=tuple)
    study_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)


class DesignTableParseIssue(JsonModel):
    """One issue while parsing a design table row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class RejectedDesignTableRow(JsonModel):
    """One rejected design-table row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[DesignTableParseIssue, ...] = Field(default_factory=tuple)


class DesignTableParseReport(JsonModel):
    """Stable parse report for study design TSV ingestion."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[StudyMetadataRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedDesignTableRow, ...] = Field(default_factory=tuple)


class ExperimentalDesignValidationIssue(JsonModel):
    """One deterministic experimental design validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition_id: str | None = None


class ExperimentalDesignValidationReport(JsonModel):
    """Validation report for study metadata experimental design entries."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: tuple[ExperimentalDesignValidationIssue, ...] = Field(default_factory=tuple)


class FractionationRecord(JsonModel):
    """One fractionation entry connecting sample metadata and evidence aggregation."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    fraction_id: str = Field(..., min_length=1)
    fraction_number: int = Field(..., ge=1)
    method: str = Field(..., min_length=1)
    pooled: bool = False
    peptide_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    protein_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)


class FractionationAggregationReport(JsonModel):
    """Fractionation summary and aggregation links to peptide/protein evidence."""

    model_config = ConfigDict(extra="forbid")

    fraction_count: int = Field(..., ge=0)
    pooled_fraction_count: int = Field(..., ge=0)
    methods: tuple[str, ...] = Field(default_factory=tuple)
    peptide_evidence_count: int = Field(..., ge=0)
    protein_evidence_count: int = Field(..., ge=0)
    records: tuple[FractionationRecord, ...] = Field(default_factory=tuple)


class InstrumentRunRecord(JsonModel):
    """One instrument run metadata row."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    instrument_id: str = Field(..., min_length=1)
    acquisition_method: str = Field(..., min_length=1)
    acquisition_date: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    run_order: int = Field(..., ge=1)
    qc_sample: bool = False


class InstrumentRunSummaryReport(JsonModel):
    """Summary report over instrument runs and QC sampling context."""

    model_config = ConfigDict(extra="forbid")

    run_count: int = Field(..., ge=0)
    instrument_count: int = Field(..., ge=0)
    batch_count: int = Field(..., ge=0)
    qc_sample_count: int = Field(..., ge=0)
    methods: tuple[str, ...] = Field(default_factory=tuple)
    records: tuple[InstrumentRunRecord, ...] = Field(default_factory=tuple)


class SampleLineageCoverageEntry(JsonModel):
    """Lineage coverage for one sample across analysis surfaces."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    in_identification: bool
    in_quant: bool
    in_ptm: bool
    in_qc: bool
    in_evidence: bool
    in_lab: bool
    missing_surfaces: tuple[str, ...] = Field(default_factory=tuple)


class SampleLineageReport(JsonModel):
    """Sample-lineage report connecting metadata to analysis outputs."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[SampleLineageCoverageEntry, ...] = Field(default_factory=tuple)
    fully_traced_sample_count: int = Field(..., ge=0)
    missing_lineage_sample_count: int = Field(..., ge=0)


class PlateLayoutEntry(JsonModel):
    """One sample/control occupancy row in a plate layout."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    replicate_id: str = Field(..., min_length=1)
    well_position: str = Field(..., min_length=2)
    control: bool = False
    randomized: bool = False


class PlateLayoutValidationIssue(JsonModel):
    """One issue found while validating a plate layout."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    sample_id: str | None = None
    well_position: str | None = None


class PlateLayoutValidationReport(JsonModel):
    """Validation report for plate layouts used by lab handoff."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: tuple[PlateLayoutValidationIssue, ...] = Field(default_factory=tuple)


class LabRequestTarget(JsonModel):
    """One assay target entry in a lab request schema."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    assay_type: str = Field(..., min_length=1)
    expected_evidence: tuple[str, ...] = Field(default_factory=tuple)


class LabRequestSchema(JsonModel):
    """Structured lab request with targets, samples, controls, and constraints."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(..., min_length=1)
    method: str = Field(..., min_length=1)
    target_entries: tuple[LabRequestTarget, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    control_ids: tuple[str, ...] = Field(default_factory=tuple)
    constraints: tuple[str, ...] = Field(default_factory=tuple)


class LabRequestValidationIssue(JsonModel):
    """One issue for lab-request schema validation."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class LabRequestValidationReport(JsonModel):
    """Validation report for lab request schema surfaces."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: tuple[LabRequestValidationIssue, ...] = Field(default_factory=tuple)


class LabHandoffExportBundle(JsonModel):
    """Lab handoff export payloads in JSON and TSV forms."""

    model_config = ConfigDict(extra="forbid")

    request_json: str = Field(..., min_length=1)
    plate_layout_tsv: str = Field(..., min_length=1)
    advisory_label: str = Field(..., min_length=1)
    executable_label: str = Field(..., min_length=1)


class PlannedLabOutcome(JsonModel):
    """One planned lab outcome expectation for a target/sample pair."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    expected_state: str = Field(..., min_length=1)
    planned_note: str = ""


class ObservedLabOutcome(JsonModel):
    """One observed lab outcome measurement for a target/sample pair."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    observed_state: str = Field(..., min_length=1)
    observed_note: str = ""


class LabOutcomeReconciliationEntry(JsonModel):
    """Reconciled planned-vs-observed outcome entry without destructive overwrite."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    expected_state: str = Field(..., min_length=1)
    observed_state: str | None = None
    matched: bool
    evidence_state: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class LabOutcomeReconciliationReport(JsonModel):
    """Summary report for planned-vs-observed lab outcomes."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[LabOutcomeReconciliationEntry, ...] = Field(default_factory=tuple)
    matched_count: int = Field(..., ge=0)
    mismatched_count: int = Field(..., ge=0)
    unobserved_count: int = Field(..., ge=0)


_FRACTION_RE = re.compile(r"^F[1-9][0-9]*$")
_CHANNEL_RE = re.compile(r"^(12[6-9]|13[01])[NC]?$")
_WELL_RE = re.compile(r"^[A-H](?:[1-9]|1[0-2])$")


def build_study_metadata_model(
    records: tuple[StudyMetadataRecord, ...],
) -> StudyMetadataModel:
    """Build study metadata model with deterministic collection summaries."""
    return StudyMetadataModel(
        records=records,
        study_count=len({record.study_id for record in records}),
        sample_count=len({record.sample_id for record in records}),
        run_count=len({record.run_id for record in records}),
    )


def parse_study_design_table(path: Path) -> DesignTableParseReport:
    """Parse a study design TSV into normalized study metadata records."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("study design table must include a header row")
        required = (
            "study_id",
            "cohort_id",
            "condition_id",
            "sample_id",
            "replicate_id",
            "fraction_id",
            "instrument_id",
            "run_id",
            "batch_id",
        )
        for column in required:
            if column not in reader.fieldnames:
                raise ValueError(f"missing required design-table column {column!r}")
        accepted: list[StudyMetadataRecord] = []
        rejected: list[RejectedDesignTableRow] = []
        for row_number, row in enumerate(reader, start=2):
            raw_fields = {
                str(key): str(value or "") for key, value in row.items() if key
            }
            issues: list[DesignTableParseIssue] = []
            for column in required:
                if not raw_fields.get(column, "").strip():
                    issues.append(
                        DesignTableParseIssue(
                            row_number=row_number,
                            code=f"missing_{column}",
                            message=f"required column {column!r} is missing or blank",
                        )
                    )
            if issues:
                rejected.append(
                    RejectedDesignTableRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=tuple(issues),
                    )
                )
                continue
            accepted.append(
                StudyMetadataRecord(
                    study_id=raw_fields["study_id"].strip(),
                    cohort_id=raw_fields["cohort_id"].strip(),
                    condition_id=raw_fields["condition_id"].strip(),
                    sample_id=raw_fields["sample_id"].strip(),
                    replicate_id=raw_fields["replicate_id"].strip(),
                    fraction_id=raw_fields["fraction_id"].strip(),
                    instrument_id=raw_fields["instrument_id"].strip(),
                    run_id=raw_fields["run_id"].strip(),
                    batch_id=raw_fields["batch_id"].strip(),
                    multiplex_channel=raw_fields.get("multiplex_channel", "").strip()
                    or None,
                    spectra_file=raw_fields.get("spectra_file", "").strip() or None,
                )
            )
    return DesignTableParseReport(
        total_rows=len(accepted) + len(rejected),
        accepted_records=tuple(accepted),
        rejected_rows=tuple(rejected),
    )


def validate_experimental_design_records(
    records: tuple[StudyMetadataRecord, ...],
    *,
    expected_spectra_files: tuple[str, ...] = (),
) -> ExperimentalDesignValidationReport:
    """Reject inconsistent experimental design entries with deterministic issue reports."""
    issues: list[ExperimentalDesignValidationIssue] = []
    seen_samples: set[str] = set()
    condition_counts: dict[str, int] = {}
    expected_files = set(expected_spectra_files)
    for record in records:
        if record.sample_id in seen_samples:
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="duplicate_sample_id",
                    message="sample_id appears more than once in the design table",
                    sample_id=record.sample_id,
                    condition_id=record.condition_id,
                )
            )
        else:
            seen_samples.add(record.sample_id)
        condition_counts[record.condition_id] = (
            condition_counts.get(record.condition_id, 0) + 1
        )
        if not _FRACTION_RE.match(record.fraction_id):
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="invalid_fraction_id",
                    message="fraction_id must match F<number> pattern such as F1",
                    sample_id=record.sample_id,
                    condition_id=record.condition_id,
                )
            )
        if record.multiplex_channel and not _CHANNEL_RE.match(record.multiplex_channel):
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="invalid_multiplex_channel",
                    message="multiplex_channel is not a recognized reporter-channel token",
                    sample_id=record.sample_id,
                    condition_id=record.condition_id,
                )
            )
        if expected_files and (
            record.spectra_file is None or record.spectra_file not in expected_files
        ):
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="inconsistent_spectra_file",
                    message="spectra_file is missing from expected file manifests",
                    sample_id=record.sample_id,
                    condition_id=record.condition_id,
                )
            )
    for condition_id, count in sorted(condition_counts.items()):
        if count < 2:
            issues.append(
                ExperimentalDesignValidationIssue(
                    code="missing_replicates",
                    message="condition has fewer than two replicate samples",
                    condition_id=condition_id,
                )
            )
    return ExperimentalDesignValidationReport(valid=not issues, issues=tuple(issues))


def build_fractionation_aggregation_report(
    records: tuple[FractionationRecord, ...],
) -> FractionationAggregationReport:
    """Build deterministic fractionation summary linked to peptide/protein evidence."""
    return FractionationAggregationReport(
        fraction_count=len(records),
        pooled_fraction_count=sum(1 for record in records if record.pooled),
        methods=tuple(sorted({record.method for record in records})),
        peptide_evidence_count=len(
            {token for record in records for token in record.peptide_evidence_ids}
        ),
        protein_evidence_count=len(
            {token for record in records for token in record.protein_evidence_ids}
        ),
        records=records,
    )


def build_instrument_run_summary_report(
    records: tuple[InstrumentRunRecord, ...],
) -> InstrumentRunSummaryReport:
    """Build deterministic instrument-run summary including QC run tracking."""
    return InstrumentRunSummaryReport(
        run_count=len(records),
        instrument_count=len({record.instrument_id for record in records}),
        batch_count=len({record.batch_id for record in records}),
        qc_sample_count=sum(1 for record in records if record.qc_sample),
        methods=tuple(sorted({record.acquisition_method for record in records})),
        records=tuple(
            sorted(records, key=lambda record: (record.batch_id, record.run_order))
        ),
    )


def build_sample_lineage_report(
    metadata_records: tuple[StudyMetadataRecord, ...],
    *,
    identification_samples: tuple[str, ...],
    quant_samples: tuple[str, ...],
    ptm_samples: tuple[str, ...],
    qc_samples: tuple[str, ...],
    evidence_samples: tuple[str, ...],
    lab_samples: tuple[str, ...],
) -> SampleLineageReport:
    """Build lineage report connecting analysis surfaces back to study metadata samples."""
    identification = set(identification_samples)
    quant = set(quant_samples)
    ptm = set(ptm_samples)
    qc = set(qc_samples)
    evidence = set(evidence_samples)
    lab = set(lab_samples)
    entries: list[SampleLineageCoverageEntry] = []
    for sample_id in sorted({record.sample_id for record in metadata_records}):
        missing = []
        in_identification = sample_id in identification
        in_quant = sample_id in quant
        in_ptm = sample_id in ptm
        in_qc = sample_id in qc
        in_evidence = sample_id in evidence
        in_lab = sample_id in lab
        if not in_identification:
            missing.append("identification")
        if not in_quant:
            missing.append("quant")
        if not in_ptm:
            missing.append("ptm")
        if not in_qc:
            missing.append("qc")
        if not in_evidence:
            missing.append("evidence")
        if not in_lab:
            missing.append("lab")
        entries.append(
            SampleLineageCoverageEntry(
                sample_id=sample_id,
                in_identification=in_identification,
                in_quant=in_quant,
                in_ptm=in_ptm,
                in_qc=in_qc,
                in_evidence=in_evidence,
                in_lab=in_lab,
                missing_surfaces=tuple(missing),
            )
        )
    return SampleLineageReport(
        entries=tuple(entries),
        fully_traced_sample_count=sum(
            1 for entry in entries if not entry.missing_surfaces
        ),
        missing_lineage_sample_count=sum(
            1 for entry in entries if entry.missing_surfaces
        ),
    )


def validate_plate_layout(
    entries: tuple[PlateLayoutEntry, ...],
    *,
    capacity: int = 96,
) -> PlateLayoutValidationReport:
    """Validate plate layout positions, controls, randomization, replicates, and capacity."""
    issues: list[PlateLayoutValidationIssue] = []
    if len(entries) > capacity:
        issues.append(
            PlateLayoutValidationIssue(
                code="capacity_exceeded",
                message="plate layout exceeds configured plate capacity",
            )
        )
    seen_wells: set[str] = set()
    replicate_counts: dict[str, int] = {}
    randomized_count = 0
    control_count = 0
    for entry in entries:
        if not _WELL_RE.match(entry.well_position):
            issues.append(
                PlateLayoutValidationIssue(
                    code="invalid_well_position",
                    message="well_position must match A1..H12",
                    sample_id=entry.sample_id,
                    well_position=entry.well_position,
                )
            )
        if entry.well_position in seen_wells:
            issues.append(
                PlateLayoutValidationIssue(
                    code="duplicate_well_position",
                    message="well_position is occupied by multiple entries",
                    sample_id=entry.sample_id,
                    well_position=entry.well_position,
                )
            )
        else:
            seen_wells.add(entry.well_position)
        replicate_counts[entry.sample_id] = replicate_counts.get(entry.sample_id, 0) + 1
        if entry.randomized:
            randomized_count += 1
        if entry.control:
            control_count += 1
    if control_count == 0:
        issues.append(
            PlateLayoutValidationIssue(
                code="missing_controls",
                message="plate layout must include at least one control entry",
            )
        )
    if randomized_count == 0:
        issues.append(
            PlateLayoutValidationIssue(
                code="missing_randomization",
                message="plate layout must include randomized positions",
            )
        )
    for sample_id, count in sorted(replicate_counts.items()):
        if count < 2:
            issues.append(
                PlateLayoutValidationIssue(
                    code="missing_replicate_layout",
                    message="sample appears fewer than two times in the plate layout",
                    sample_id=sample_id,
                )
            )
    return PlateLayoutValidationReport(valid=not issues, issues=tuple(issues))


def validate_lab_request_schema(
    request: LabRequestSchema,
) -> LabRequestValidationReport:
    """Validate lab request schema integrity for assay planning and handoff."""
    issues: list[LabRequestValidationIssue] = []
    if not request.target_entries:
        issues.append(
            LabRequestValidationIssue(
                code="missing_targets",
                message="lab request must include at least one target entry",
            )
        )
    if not request.sample_ids:
        issues.append(
            LabRequestValidationIssue(
                code="missing_samples",
                message="lab request must include at least one sample",
            )
        )
    if not request.control_ids:
        issues.append(
            LabRequestValidationIssue(
                code="missing_controls",
                message="lab request must include at least one control",
            )
        )
    if request.method.lower() not in {"prm", "srm", "dda_validation", "dia_validation"}:
        issues.append(
            LabRequestValidationIssue(
                code="unsupported_method",
                message="lab request method is not supported by this schema validator",
            )
        )
    for target in request.target_entries:
        if not target.expected_evidence:
            issues.append(
                LabRequestValidationIssue(
                    code="target_missing_expected_evidence",
                    message=f"target {target.target_id!r} does not include expected evidence requirements",
                )
            )
    return LabRequestValidationReport(valid=not issues, issues=tuple(issues))


def build_lab_handoff_export_bundle(
    request: LabRequestSchema,
    plate_entries: tuple[PlateLayoutEntry, ...],
) -> LabHandoffExportBundle:
    """Export lab handoff request sheets and plate layouts in JSON and TSV formats."""
    request_payload = {
        "request_id": request.request_id,
        "method": request.method,
        "targets": [target.to_dict() for target in request.target_entries],
        "sample_ids": list(request.sample_ids),
        "control_ids": list(request.control_ids),
        "constraints": list(request.constraints),
        "label": "advisory",
    }
    header = "sample_id\treplicate_id\twell_position\tcontrol\trandomized\tlabel"
    rows = [
        "\t".join(
            (
                entry.sample_id,
                entry.replicate_id,
                entry.well_position,
                "1" if entry.control else "0",
                "1" if entry.randomized else "0",
                "executable",
            )
        )
        for entry in plate_entries
    ]
    return LabHandoffExportBundle(
        request_json=json.dumps(request_payload, sort_keys=True, separators=(",", ":")),
        plate_layout_tsv="\n".join([header, *rows]) + ("\n" if rows else ""),
        advisory_label="advisory",
        executable_label="executable",
    )


def reconcile_planned_and_observed_lab_outcomes(
    planned: tuple[PlannedLabOutcome, ...],
    observed: tuple[ObservedLabOutcome, ...],
) -> LabOutcomeReconciliationReport:
    """Ingest observed outcomes without mutating planned expectations and update evidence state."""
    observed_map = {(entry.target_id, entry.sample_id): entry for entry in observed}
    entries: list[LabOutcomeReconciliationEntry] = []
    for planned_entry in planned:
        observed_entry = observed_map.get(
            (planned_entry.target_id, planned_entry.sample_id)
        )
        if observed_entry is None:
            entries.append(
                LabOutcomeReconciliationEntry(
                    target_id=planned_entry.target_id,
                    sample_id=planned_entry.sample_id,
                    expected_state=planned_entry.expected_state,
                    observed_state=None,
                    matched=False,
                    evidence_state="awaiting_observation",
                    note="planned expectation preserved while observed outcome is still missing",
                )
            )
            continue
        matched = observed_entry.observed_state == planned_entry.expected_state
        entries.append(
            LabOutcomeReconciliationEntry(
                target_id=planned_entry.target_id,
                sample_id=planned_entry.sample_id,
                expected_state=planned_entry.expected_state,
                observed_state=observed_entry.observed_state,
                matched=matched,
                evidence_state="confirmed" if matched else "contradicted",
                note="observed outcome aligned with planned expectation"
                if matched
                else "observed outcome diverged from planned expectation without altering planned state",
            )
        )
    return LabOutcomeReconciliationReport(
        entries=tuple(entries),
        matched_count=sum(1 for entry in entries if entry.matched),
        mismatched_count=sum(
            1
            for entry in entries
            if entry.observed_state is not None and not entry.matched
        ),
        unobserved_count=sum(1 for entry in entries if entry.observed_state is None),
    )
