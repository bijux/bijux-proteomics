# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Laboratory-facing action packets derived from explicit QC failures."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.lab.background import BackgroundComparisonEntry
from bijux_proteomics.lab.cohort import CohortBalanceEntry
from bijux_proteomics.lab.contamination import ContaminantClass, ContaminationClassificationEntry
from bijux_proteomics.lab.digestion_diagnosis import DigestionDiagnosisEntry, DigestionStatus
from bijux_proteomics.lab.run_diagnosis import (
    LabQcStatus,
    RunDiagnosisEntry,
    RunFailureClass,
)
from bijux_proteomics.lab.sample_identity import SampleSwapSuspicionEntry
from bijux_proteomics.lab.standards import InternalStandardTrackingEntry
from bijux_proteomics_foundation import JsonModel


class LabActionPacket(JsonModel):
    """One lab action packet tied to an explicit QC failure row."""

    model_config = ConfigDict(extra="forbid")

    entity_type: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    problem: str = Field(..., min_length=1)
    evidence_rows: tuple[str, ...] = Field(default_factory=tuple)
    recommended_action: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(low|medium|high)$")


class LabActionAssessmentEntry(JsonModel):
    """One archived QC assessment row that can drive a lab action packet."""

    model_config = ConfigDict(extra="forbid")

    scope: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    qc_status: str = Field(..., min_length=1)
    status_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    metric_key: str | None = None
    severity: str | None = None
    disposition: str | None = None
    enforced_violation: bool | None = None
    message: str = Field(..., min_length=1)


def build_lab_action_packets(
    qc_results: tuple[object, ...],
) -> tuple[LabActionPacket, ...]:
    """Build specific lab action packets from explicit lab QC failures."""

    packets: list[LabActionPacket] = []
    for row in qc_results:
        packets.extend(_packets_for_row(row))
    return tuple(
        sorted(
            packets,
            key=lambda packet: (
                packet.entity_type,
                packet.entity_id,
                packet.problem,
                packet.severity,
            ),
        )
    )


def render_lab_action_packets_tsv(packets: tuple[LabActionPacket, ...]) -> str:
    """Render lab action packets as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_type",
            "entity_id",
            "problem",
            "evidence_rows",
            "recommended_action",
            "severity",
        )
    )
    for packet in packets:
        writer.writerow(
            (
                packet.entity_type,
                packet.entity_id,
                packet.problem,
                ";".join(packet.evidence_rows),
                packet.recommended_action,
                packet.severity,
            )
        )
    return buffer.getvalue()


def parse_lab_action_packet_tsv(path: Path) -> tuple[LabActionPacket, ...]:
    """Parse archived lab action packet rows from a stable TSV surface."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("lab action packet TSV must include a header row")
        return tuple(
            LabActionPacket(
                entity_type=(row.get("entity_type") or "").strip(),
                entity_id=(row.get("entity_id") or "").strip(),
                problem=(row.get("problem") or "").strip(),
                evidence_rows=_split_semicolon_field(row.get("evidence_rows")),
                recommended_action=(row.get("recommended_action") or "").strip(),
                severity=(row.get("severity") or "").strip(),
            )
            for row in reader
        )


def parse_lab_action_assessment_tsv(path: Path) -> tuple[LabActionAssessmentEntry, ...]:
    """Parse archived QC assessment rows that can be projected into action packets."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("lab action assessment TSV must include a header row")
        return tuple(
            LabActionAssessmentEntry(
                scope=(row.get("scope") or "").strip(),
                entity_id=(row.get("entity_id") or "").strip(),
                qc_status=(row.get("qc_status") or "").strip(),
                status_reason_codes=_split_semicolon_field(
                    row.get("status_reason_codes")
                ),
                metric_key=_optional_value(row.get("metric_key")),
                severity=_optional_value(row.get("severity")),
                disposition=_optional_value(row.get("disposition")),
                enforced_violation=_optional_bool(row.get("enforced_violation")),
                message=(row.get("message") or "").strip() or "QC assessment failed",
            )
            for row in reader
        )


def build_lab_action_packets_from_qc_assessment(
    entries: tuple[LabActionAssessmentEntry, ...],
) -> tuple[LabActionPacket, ...]:
    """Build archived lab action packets from failed run or sample QC assessment rows."""

    packets: list[LabActionPacket] = []
    for entry in entries:
        status = entry.qc_status.strip().lower()
        if status in {"pass", "ok"}:
            continue
        if not _is_actionable_assessment_status(status):
            continue
        packets.append(
            LabActionPacket(
                entity_type=entry.scope.strip().lower(),
                entity_id=entry.entity_id,
                problem=_assessment_problem(entry),
                evidence_rows=_assessment_evidence_rows(entry),
                recommended_action=_assessment_recommended_action(entry),
                severity=_assessment_packet_severity(entry),
            )
        )
    return tuple(
        sorted(
            packets,
            key=lambda packet: (
                packet.entity_type,
                packet.entity_id,
                packet.problem,
                packet.severity,
            ),
        )
    )


def _packets_for_row(row: object) -> tuple[LabActionPacket, ...]:
    if isinstance(row, RunDiagnosisEntry):
        return _packets_for_run_diagnosis(row)
    if isinstance(row, DigestionDiagnosisEntry):
        return _packets_for_digestion(row)
    if isinstance(row, ContaminationClassificationEntry):
        return _packets_for_contamination(row)
    if isinstance(row, BackgroundComparisonEntry):
        return _packets_for_background(row)
    if isinstance(row, InternalStandardTrackingEntry):
        return _packets_for_internal_standard(row)
    if isinstance(row, SampleSwapSuspicionEntry):
        return _packets_for_sample_identity(row)
    if isinstance(row, CohortBalanceEntry):
        return _packets_for_cohort(row)
    return ()


def _split_semicolon_field(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(token.strip() for token in value.split(";") if token.strip())


def _optional_value(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _optional_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return None


def _is_actionable_assessment_status(status: str) -> bool:
    return status in {"fail", "failed", "block", "blocked", "caution", "warn", "warning"}


def _assessment_problem(entry: LabActionAssessmentEntry) -> str:
    if entry.status_reason_codes:
        return entry.status_reason_codes[0]
    return "qc_failure"


def _assessment_evidence_rows(
    entry: LabActionAssessmentEntry,
) -> tuple[str, ...]:
    rows = [
        f"scope={entry.scope}",
        f"entity_id={entry.entity_id}",
        f"qc_status={entry.qc_status}",
    ]
    rows.extend(
        f"reason_code={reason_code}" for reason_code in entry.status_reason_codes
    )
    if entry.metric_key is not None:
        rows.append(f"metric_key={entry.metric_key}")
    if entry.severity is not None:
        rows.append(f"severity={entry.severity}")
    if entry.disposition is not None:
        rows.append(f"disposition={entry.disposition}")
    if entry.enforced_violation is not None:
        rows.append(
            f"enforced_violation={str(entry.enforced_violation).lower()}"
        )
    rows.append(f"message={entry.message}")
    return tuple(rows)


def _assessment_packet_severity(entry: LabActionAssessmentEntry) -> str:
    status = entry.qc_status.strip().lower()
    severity = (entry.severity or "").strip().lower()
    if status in {"fail", "failed", "block", "blocked"}:
        return "high"
    if severity in {"failed", "critical", "high"}:
        return "high"
    if entry.enforced_violation is True:
        return "high"
    if status in {"caution", "warn", "warning"}:
        return "medium"
    return "low"


def _assessment_recommended_action(entry: LabActionAssessmentEntry) -> str:
    reason_codes = set(entry.status_reason_codes)
    scope = entry.scope.strip().lower()
    if "identification_rate_low" in reason_codes:
        return (
            "review precursor isolation, fragmentation yield, and search-ready "
            "identification depth before accepting or rerunning this QC-failed "
            f"{scope}"
        )
    if "chromatography_instability" in reason_codes:
        return (
            "inspect column performance, gradient delivery, and retention-time "
            f"stability before accepting this QC-failed {scope}"
        )
    if "intensity_instability" in reason_codes:
        return (
            "check spray stability, ion transmission, and loading consistency "
            f"before using this QC-failed {scope} quantitatively"
        )
    if scope == "sample":
        return (
            "hold sample-level interpretation and review upstream preparation and "
            "QC evidence before accepting this sample"
        )
    return (
        "exclude this QC-failed run from biological interpretation until the "
        "preserved failure reasons have been reviewed and resolved"
    )


def _packets_for_run_diagnosis(row: RunDiagnosisEntry) -> tuple[LabActionPacket, ...]:
    if row.status is LabQcStatus.PASSED or row.failure_class is RunFailureClass.NO_FAILURE:
        return ()
    actions = {
        RunFailureClass.CHROMATOGRAPHY_FAILURE: (
            "run",
            row.run_id,
            row.primary_reason,
            (
                f"run_id={row.run_id}",
                f"failure_class={row.failure_class.value}",
                f"primary_reason={row.primary_reason}",
            ),
            "inspect column performance, gradient delivery, and retention-time stability before accepting this run",
            "high" if row.status is LabQcStatus.FAIL else "medium",
        ),
        RunFailureClass.IDENTIFICATION_FAILURE: (
            "run",
            row.run_id,
            row.primary_reason,
            (
                f"run_id={row.run_id}",
                f"failure_class={row.failure_class.value}",
                f"primary_reason={row.primary_reason}",
            ),
            "review precursor isolation, fragmentation yield, and search-ready identification depth for this run",
            "high" if row.status is LabQcStatus.FAIL else "medium",
        ),
        RunFailureClass.INTENSITY_FAILURE: (
            "run",
            row.run_id,
            row.primary_reason,
            (
                f"run_id={row.run_id}",
                f"failure_class={row.failure_class.value}",
                f"primary_reason={row.primary_reason}",
            ),
            "check spray stability, ion transmission, and loading consistency before using this run quantitatively",
            "high" if row.status is LabQcStatus.FAIL else "medium",
        ),
        RunFailureClass.MIXED_FAILURE: (
            "run",
            row.run_id,
            row.primary_reason,
            (
                f"run_id={row.run_id}",
                f"failure_class={row.failure_class.value}",
                f"primary_reason={row.primary_reason}",
                *tuple(f"secondary_reason={reason}" for reason in row.secondary_reasons),
            ),
            "triage chromatography, identification, and signal problems together because multiple run-failure modes co-occur",
            "high",
        ),
    }
    action = actions.get(row.failure_class)
    if action is None:
        return ()
    return (
        LabActionPacket(
            entity_type=action[0],
            entity_id=action[1],
            problem=action[2],
            evidence_rows=action[3],
            recommended_action=action[4],
            severity=action[5],
        ),
    )


def _packets_for_digestion(row: DigestionDiagnosisEntry) -> tuple[LabActionPacket, ...]:
    if row.digestion_status is DigestionStatus.PASSED:
        return ()
    actions = {
        DigestionStatus.INEFFICIENT_DIGESTION: (
            "sample",
            row.sample_id,
            "inefficient_digestion",
            (
                f"sample_id={row.sample_id}",
                f"missed_cleavage_rate={row.missed_cleavage_rate:.4f}",
            ),
            "review digestion time, enzyme amount, and denaturation efficiency for this sample",
            "medium",
        ),
        DigestionStatus.LOW_SPECIFICITY: (
            "sample",
            row.sample_id,
            "low_specificity_digestion",
            (
                f"sample_id={row.sample_id}",
                f"semi_specific_rate={row.semi_specific_rate:.4f}",
                f"non_specific_rate={row.non_specific_rate:.4f}",
            ),
            "audit proteolysis conditions and cleanup because non-specific cleavage burden is elevated",
            "medium",
        ),
        DigestionStatus.ENZYME_MISMATCH: (
            "sample",
            row.sample_id,
            "declared_enzyme_mismatch",
            (
                f"sample_id={row.sample_id}",
                f"missed_cleavage_rate={row.missed_cleavage_rate:.4f}",
                f"semi_specific_rate={row.semi_specific_rate:.4f}",
            ),
            "verify the declared digestion enzyme and sample-preparation record before interpreting this sample",
            "high",
        ),
    }
    action = actions.get(row.digestion_status)
    if action is None:
        return ()
    return (
        LabActionPacket(
            entity_type=action[0],
            entity_id=action[1],
            problem=action[2],
            evidence_rows=action[3],
            recommended_action=action[4],
            severity=action[5],
        ),
    )


def _packets_for_contamination(
    row: ContaminationClassificationEntry,
) -> tuple[LabActionPacket, ...]:
    if row.intensity_fraction <= 0.0:
        return ()
    if row.contaminant_class is ContaminantClass.UNKNOWN and row.intensity_fraction < 0.05:
        return ()
    return (
        LabActionPacket(
            entity_type="sample",
            entity_id=row.sample_id,
            problem=f"{row.contaminant_class.value}_contamination",
            evidence_rows=(
                f"sample_id={row.sample_id}",
                f"contaminant_class={row.contaminant_class.value}",
                f"top_contaminant_proteins={';'.join(row.top_contaminant_proteins)}",
                f"intensity_fraction={row.intensity_fraction:.4f}",
            ),
            recommended_action=row.action_hint,
            severity="high" if row.intensity_fraction >= 0.1 else "medium",
        ),
    )


def _packets_for_background(row: BackgroundComparisonEntry) -> tuple[LabActionPacket, ...]:
    if not row.background_flag:
        return ()
    return (
        LabActionPacket(
            entity_type="sample_entity",
            entity_id=f"{row.sample_id}:{row.entity_id}",
            problem="blank_dominated_background",
            evidence_rows=(
                f"sample_id={row.sample_id}",
                f"entity_id={row.entity_id}",
                f"blank_intensity={row.blank_intensity:.4f}",
                f"sample_intensity={row.sample_intensity:.4f}",
                f"background_ratio={row.background_ratio:.4f}",
            ),
            recommended_action="review carryover, wash sufficiency, and blank subtraction before accepting this entity in the affected sample",
            severity="medium",
        ),
    )


def _packets_for_internal_standard(
    row: InternalStandardTrackingEntry,
) -> tuple[LabActionPacket, ...]:
    if not row.drift_flag:
        return ()
    problem = "internal_standard_missing" if row.missing else "internal_standard_drift"
    recommended_action = (
        "verify spike-in preparation and acquisition because this internal standard is missing in the affected sample"
        if row.missing
        else "review spike-in amount, injection consistency, and instrument response because this internal standard drifted"
    )
    severity = "high" if row.missing else "medium"
    return (
        LabActionPacket(
            entity_type="standard_sample",
            entity_id=f"{row.sample_id}:{row.standard_id}",
            problem=problem,
            evidence_rows=(
                f"sample_id={row.sample_id}",
                f"standard_id={row.standard_id}",
                f"intensity={row.intensity:.4f}",
                f"cv={row.cv:.4f}",
                f"missing={str(row.missing).lower()}",
            ),
            recommended_action=recommended_action,
            severity=severity,
        ),
    )


def _packets_for_sample_identity(
    row: SampleSwapSuspicionEntry,
) -> tuple[LabActionPacket, ...]:
    if row.nearest_neighbor_group == row.expected_group or row.swap_suspicion_score < 0.8:
        return ()
    return (
        LabActionPacket(
            entity_type="sample",
            entity_id=row.sample_id,
            problem="sample_swap_suspicion",
            evidence_rows=(
                f"sample_id={row.sample_id}",
                f"expected_group={row.expected_group}",
                f"nearest_neighbor_sample={row.nearest_neighbor_sample}",
                f"nearest_neighbor_group={row.nearest_neighbor_group}",
                f"swap_suspicion_score={row.swap_suspicion_score:.4f}",
            ),
            recommended_action="audit sample labeling and plate map provenance for this sample; do not relabel automatically from similarity alone",
            severity="high",
        ),
    )


def _packets_for_cohort(row: CohortBalanceEntry) -> tuple[LabActionPacket, ...]:
    if row.confounded_with_condition:
        severity = "high"
        problem = "condition_confounded_covariate"
    elif row.imbalance_score >= 0.6:
        severity = "medium"
        problem = "material_cohort_imbalance"
    else:
        return ()
    return (
        LabActionPacket(
            entity_type="covariate",
            entity_id=row.covariate,
            problem=problem,
            evidence_rows=(
                f"covariate={row.covariate}",
                f"group_counts={row.group_counts}",
                f"imbalance_score={row.imbalance_score:.4f}",
            ),
            recommended_action=row.analysis_warning,
            severity=severity,
        ),
    )


__all__ = [
    "LabActionAssessmentEntry",
    "LabActionPacket",
    "build_lab_action_packets",
    "build_lab_action_packets_from_qc_assessment",
    "parse_lab_action_assessment_tsv",
    "parse_lab_action_packet_tsv",
    "render_lab_action_packets_tsv",
]
