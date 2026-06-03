# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protocol-consistency diagnostics over declared lab context and observed data."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.lab.protocol_context import (
    DigestionEnzyme,
    EnrichmentType,
    LabelingMethod,
    LabProtocolContextEntry,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.lab.qc import LcmsRunQcReport
    from bijux_proteomics.multiplex.reporter_ion_import import TmtReporterImportReport
    from bijux_proteomics.ptm.contracts import PtmEvidenceParseReport


class ProtocolConsistencyAxis(StrEnum):
    """Stable axes across declared protocol and observed evidence."""

    DIGESTION = "digestion"
    LABELING = "labeling"
    ENRICHMENT = "enrichment"


class ProtocolConsistencySeverity(StrEnum):
    """Stable severity for protocol-consistency diagnostics."""

    CAUTION = "caution"
    BLOCKING = "blocking"


class ProtocolConsistencyStatus(StrEnum):
    """Compact overall protocol-consistency status."""

    PASSED = "pass"
    CAUTION = "caution"
    BLOCKING = "blocking"


class ProtocolConsistencyDiagnostic(JsonModel):
    """One declared-protocol versus observed-data mismatch or assessment gap."""

    model_config = ConfigDict(extra="forbid")

    axis: ProtocolConsistencyAxis
    code: str = Field(..., min_length=1)
    severity: ProtocolConsistencySeverity
    expected: str = Field(..., min_length=1)
    observed: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ProtocolConsistencySummary(JsonModel):
    """Compact protocol-consistency summary."""

    model_config = ConfigDict(extra="forbid")

    status: ProtocolConsistencyStatus
    blocking_diagnostic_count: int = Field(..., ge=0)
    caution_diagnostic_count: int = Field(..., ge=0)
    assessed_axes: tuple[ProtocolConsistencyAxis, ...] = Field(default_factory=tuple)


class ProtocolConsistencyReport(JsonModel):
    """Owned report of whether observed evidence matches the declared protocol."""

    model_config = ConfigDict(extra="forbid")

    protocol_context: LabProtocolContextEntry
    diagnostics: tuple[ProtocolConsistencyDiagnostic, ...] = Field(
        default_factory=tuple
    )
    summary: ProtocolConsistencySummary
    note: str = Field(..., min_length=1)


def build_protocol_consistency_report(
    protocol_context: LabProtocolContextEntry,
    *,
    run_qc_report: LcmsRunQcReport | None = None,
    reporter_import_report: TmtReporterImportReport | None = None,
    ptm_evidence_report: PtmEvidenceParseReport | None = None,
    reporter_input_issue: str | None = None,
    ptm_input_issue: str | None = None,
) -> ProtocolConsistencyReport:
    """Compare declared protocol context with observed digestion, TMT, and PTM evidence."""

    diagnostics: list[ProtocolConsistencyDiagnostic] = []
    assessed_axes: set[ProtocolConsistencyAxis] = set()

    _append_digestion_diagnostics(
        diagnostics,
        assessed_axes,
        protocol_context=protocol_context,
        run_qc_report=run_qc_report,
    )
    _append_labeling_diagnostics(
        diagnostics,
        assessed_axes,
        protocol_context=protocol_context,
        reporter_import_report=reporter_import_report,
        reporter_input_issue=reporter_input_issue,
    )
    _append_enrichment_diagnostics(
        diagnostics,
        assessed_axes,
        protocol_context=protocol_context,
        ptm_evidence_report=ptm_evidence_report,
        ptm_input_issue=ptm_input_issue,
    )

    blocking_count = sum(
        1
        for diagnostic in diagnostics
        if diagnostic.severity is ProtocolConsistencySeverity.BLOCKING
    )
    caution_count = sum(
        1
        for diagnostic in diagnostics
        if diagnostic.severity is ProtocolConsistencySeverity.CAUTION
    )
    status = ProtocolConsistencyStatus.PASSED
    if blocking_count:
        status = ProtocolConsistencyStatus.BLOCKING
    elif caution_count:
        status = ProtocolConsistencyStatus.CAUTION
    return ProtocolConsistencyReport(
        protocol_context=protocol_context,
        diagnostics=tuple(diagnostics),
        summary=ProtocolConsistencySummary(
            status=status,
            blocking_diagnostic_count=blocking_count,
            caution_diagnostic_count=caution_count,
            assessed_axes=tuple(sorted(assessed_axes)),
        ),
        note=(
            "protocol-consistency diagnostics compare declared digestion, labeling, "
            "and enrichment context with observed evidence and distinguish blocking "
            "mismatches from caution-level assessment gaps or weak agreement"
        ),
    )


def require_protocol_consistency_without_blockers(
    report: ProtocolConsistencyReport,
) -> ProtocolConsistencyReport:
    """Return a protocol-consistency report or raise on blocking mismatches."""

    blocking = tuple(
        diagnostic
        for diagnostic in report.diagnostics
        if diagnostic.severity is ProtocolConsistencySeverity.BLOCKING
    )
    if blocking:
        raise ValueError(
            "protocol consistency contains blocking diagnostics: "
            + "; ".join(
                f"{diagnostic.code} ({diagnostic.message})" for diagnostic in blocking
            )
        )
    return report


def render_protocol_consistency_tsv(report: ProtocolConsistencyReport) -> str:
    """Render protocol-consistency diagnostics as a governed TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protocol_id",
            "axis",
            "code",
            "severity",
            "expected",
            "observed",
            "message",
        )
    )
    for diagnostic in report.diagnostics:
        writer.writerow(
            (
                report.protocol_context.protocol_id,
                diagnostic.axis.value,
                diagnostic.code,
                diagnostic.severity.value,
                diagnostic.expected,
                diagnostic.observed,
                diagnostic.message,
            )
        )
    return buffer.getvalue()


def _append_digestion_diagnostics(
    diagnostics: list[ProtocolConsistencyDiagnostic],
    assessed_axes: set[ProtocolConsistencyAxis],
    *,
    protocol_context: LabProtocolContextEntry,
    run_qc_report: LcmsRunQcReport | None,
) -> None:
    if protocol_context.digestion_enzyme not in {
        DigestionEnzyme.TRYPSIN,
        DigestionEnzyme.TRYPSIN_LYSC,
        DigestionEnzyme.LYSC,
    }:
        return
    assessed_axes.add(ProtocolConsistencyAxis.DIGESTION)
    if run_qc_report is None:
        diagnostics.append(
            ProtocolConsistencyDiagnostic(
                axis=ProtocolConsistencyAxis.DIGESTION,
                code="digestion_consistency_not_assessed",
                severity=ProtocolConsistencySeverity.CAUTION,
                expected=protocol_context.digestion_enzyme.value,
                observed="no_run_qc_evidence",
                message=(
                    "declared digestion enzyme cannot be checked without observed "
                    "PSM and spectrum evidence"
                ),
            )
        )
        return
    specificity_lookup = {
        str(entry.specificity): entry.fraction
        for entry in run_qc_report.digestion_specificity
    }
    non_specific_fraction = specificity_lookup.get(
        "non_specific",
        0.0,
    )
    semi_specific_fraction = specificity_lookup.get(
        "semi_specific",
        0.0,
    )
    observed = (
        f"missed_cleavage_rate={run_qc_report.missed_cleavage_rate:.3f};"
        f"semi_specific_fraction={semi_specific_fraction:.3f};"
        f"non_specific_fraction={non_specific_fraction:.3f}"
    )
    if (
        non_specific_fraction >= 0.25
        or semi_specific_fraction >= 0.35
        or run_qc_report.missed_cleavage_rate >= 0.35
    ):
        diagnostics.append(
            ProtocolConsistencyDiagnostic(
                axis=ProtocolConsistencyAxis.DIGESTION,
                code="digestion_specificity_mismatch",
                severity=ProtocolConsistencySeverity.BLOCKING,
                expected=(
                    "tryptic or lysc-compatible digestion with mostly enzymatic peptides"
                ),
                observed=observed,
                message=(
                    "observed peptide specificity is too non-enzymatic for the "
                    "declared digestion protocol"
                ),
            )
        )
        return
    if (
        non_specific_fraction >= 0.15
        or semi_specific_fraction >= 0.2
        or run_qc_report.missed_cleavage_rate >= 0.2
    ):
        diagnostics.append(
            ProtocolConsistencyDiagnostic(
                axis=ProtocolConsistencyAxis.DIGESTION,
                code="digestion_specificity_drift",
                severity=ProtocolConsistencySeverity.CAUTION,
                expected=(
                    "low non-specific burden and modest missed-cleavage rate for "
                    "the declared digestion protocol"
                ),
                observed=observed,
                message=(
                    "observed peptide specificity weakens confidence in the "
                    "declared digestion protocol"
                ),
            )
        )


def _append_labeling_diagnostics(
    diagnostics: list[ProtocolConsistencyDiagnostic],
    assessed_axes: set[ProtocolConsistencyAxis],
    *,
    protocol_context: LabProtocolContextEntry,
    reporter_import_report: TmtReporterImportReport | None,
    reporter_input_issue: str | None,
) -> None:
    observed_channel_ids: tuple[str, ...] = ()
    observed_signal_count = 0
    if reporter_import_report is not None:
        observed_channel_ids = tuple(
            sorted(
                {
                    intensity.multiplex_channel
                    for row in reporter_import_report.accepted_rows
                    for intensity in row.channel_intensities
                    if intensity.intensity is not None and intensity.intensity > 0.0
                }
            )
        )
        observed_signal_count = sum(
            1
            for row in reporter_import_report.accepted_rows
            for intensity in row.channel_intensities
            if intensity.intensity is not None and intensity.intensity > 0.0
        )
    if protocol_context.labeling_method is LabelingMethod.TMT:
        assessed_axes.add(ProtocolConsistencyAxis.LABELING)
        if reporter_input_issue is not None:
            diagnostics.append(
                ProtocolConsistencyDiagnostic(
                    axis=ProtocolConsistencyAxis.LABELING,
                    code="reporter_channel_input_invalid",
                    severity=ProtocolConsistencySeverity.BLOCKING,
                    expected="TMT reporter-channel evidence",
                    observed=reporter_input_issue,
                    message=(
                        "declared TMT protocol requires parseable reporter-channel evidence"
                    ),
                )
            )
            return
        if reporter_import_report is None:
            diagnostics.append(
                ProtocolConsistencyDiagnostic(
                    axis=ProtocolConsistencyAxis.LABELING,
                    code="reporter_channel_evidence_not_assessed",
                    severity=ProtocolConsistencySeverity.CAUTION,
                    expected="TMT reporter-channel evidence",
                    observed="no_reporter_table_input",
                    message=(
                        "declared TMT protocol cannot be checked without observed "
                        "reporter-channel evidence"
                    ),
                )
            )
            return
        if observed_signal_count == 0:
            diagnostics.append(
                ProtocolConsistencyDiagnostic(
                    axis=ProtocolConsistencyAxis.LABELING,
                    code="missing_reporter_channel_signal",
                    severity=ProtocolConsistencySeverity.BLOCKING,
                    expected="multiple observed TMT reporter channels",
                    observed="0_positive_reporter_signals",
                    message=(
                        "declared TMT protocol is inconsistent with the observed "
                        "reporter table because no reporter-channel signal was found"
                    ),
                )
            )
            return
        if len(observed_channel_ids) < 2:
            diagnostics.append(
                ProtocolConsistencyDiagnostic(
                    axis=ProtocolConsistencyAxis.LABELING,
                    code="sparse_reporter_channel_signal",
                    severity=ProtocolConsistencySeverity.CAUTION,
                    expected="broad reporter-channel support for a TMT plex",
                    observed=(
                        f"{len(observed_channel_ids)}_channels_with_positive_signal"
                    ),
                    message=(
                        "declared TMT protocol has only sparse observed reporter-channel support"
                    ),
                )
            )
    elif reporter_import_report is not None and observed_signal_count > 0:
        assessed_axes.add(ProtocolConsistencyAxis.LABELING)
        diagnostics.append(
            ProtocolConsistencyDiagnostic(
                axis=ProtocolConsistencyAxis.LABELING,
                code="unexpected_reporter_channel_signal",
                severity=ProtocolConsistencySeverity.CAUTION,
                expected=protocol_context.labeling_method.value,
                observed=(
                    f"{len(observed_channel_ids)}_channels_with_positive_tmt_signal"
                ),
                message=(
                    "observed reporter-channel evidence does not match the declared "
                    "non-TMT labeling protocol"
                ),
            )
        )


def _append_enrichment_diagnostics(
    diagnostics: list[ProtocolConsistencyDiagnostic],
    assessed_axes: set[ProtocolConsistencyAxis],
    *,
    protocol_context: LabProtocolContextEntry,
    ptm_evidence_report: PtmEvidenceParseReport | None,
    ptm_input_issue: str | None,
) -> None:
    if protocol_context.enrichment_type is EnrichmentType.NONE:
        return
    assessed_axes.add(ProtocolConsistencyAxis.ENRICHMENT)
    if ptm_input_issue is not None:
        diagnostics.append(
            ProtocolConsistencyDiagnostic(
                axis=ProtocolConsistencyAxis.ENRICHMENT,
                code="ptm_evidence_input_invalid",
                severity=ProtocolConsistencySeverity.BLOCKING,
                expected=f"{protocol_context.enrichment_type.value}_site_evidence",
                observed=ptm_input_issue,
                message=(
                    "declared enrichment protocol requires parseable PTM evidence "
                    "to confirm the expected modified site class"
                ),
            )
        )
        return
    if ptm_evidence_report is None:
        diagnostics.append(
            ProtocolConsistencyDiagnostic(
                axis=ProtocolConsistencyAxis.ENRICHMENT,
                code="enrichment_evidence_not_assessed",
                severity=ProtocolConsistencySeverity.CAUTION,
                expected=f"{protocol_context.enrichment_type.value}_site_evidence",
                observed="no_ptm_evidence_input",
                message=(
                    "declared enrichment protocol cannot be checked without observed PTM evidence"
                ),
            )
        )
        return
    matching_record_count = sum(
        1
        for record in ptm_evidence_report.accepted_records
        if _matches_enrichment(
            record.modification_names, protocol_context.enrichment_type
        )
    )
    observed = (
        f"matching_ptm_rows={matching_record_count};"
        f"accepted_ptm_rows={len(ptm_evidence_report.accepted_records)}"
    )
    if matching_record_count == 0:
        diagnostics.append(
            ProtocolConsistencyDiagnostic(
                axis=ProtocolConsistencyAxis.ENRICHMENT,
                code="missing_expected_enrichment_sites",
                severity=ProtocolConsistencySeverity.BLOCKING,
                expected=f"{protocol_context.enrichment_type.value}_modified_sites",
                observed=observed,
                message=(
                    "declared enrichment protocol is inconsistent with the observed "
                    "PTM evidence because no matching modified sites were found"
                ),
            )
        )
        return
    if matching_record_count < 2:
        diagnostics.append(
            ProtocolConsistencyDiagnostic(
                axis=ProtocolConsistencyAxis.ENRICHMENT,
                code="sparse_expected_enrichment_sites",
                severity=ProtocolConsistencySeverity.CAUTION,
                expected=f"multiple {protocol_context.enrichment_type.value} site rows",
                observed=observed,
                message=(
                    "declared enrichment protocol has only sparse matching PTM evidence"
                ),
            )
        )


def _matches_enrichment(
    modification_names: tuple[str, ...],
    enrichment_type: EnrichmentType,
) -> bool:
    lowered = tuple(name.casefold() for name in modification_names)
    if enrichment_type is EnrichmentType.PHOSPHO:
        return any("phospho" in name or "phosphoryl" in name for name in lowered)
    if enrichment_type is EnrichmentType.ACETYL:
        return any("acetyl" in name for name in lowered)
    if enrichment_type is EnrichmentType.UBIQUITIN:
        return any(
            token in name
            for name in lowered
            for token in ("digly", "glygly", "ubiquitin", "ubiquityl")
        )
    if enrichment_type is EnrichmentType.GLYCO:
        return any("glyco" in name or "glycan" in name for name in lowered)
    return bool(modification_names)
