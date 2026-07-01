# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Review and handoff artifacts derived from QC assessments."""

from __future__ import annotations

from bijux_proteomics.lab.qc.models import (
    InstrumentBatchQcReport,
    LcmsRunQcReport,
    ProteomicsPerformanceOperation,
    ProteomicsPerformanceSnapshot,
    QcBatchAssessmentReport,
    QcEvidenceInputFile,
    QcEvidenceManifest,
    QcPublicationDecision,
    QcRunAssessmentReport,
    QcRunBundleSummary,
    QcThresholdPolicy,
)
from bijux_proteomics.lab.qc.support import (
    build_document_schema,
    format_metric_value,
    stable_sha256,
)


def build_qc_evidence_manifest(
    *,
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
    policy: QcThresholdPolicy,
    input_files: tuple[QcEvidenceInputFile, ...],
    batch_report: InstrumentBatchQcReport | None = None,
    batch_assessment: QcBatchAssessmentReport | None = None,
    benchmark: ProteomicsPerformanceSnapshot | None = None,
) -> QcEvidenceManifest:
    """Build a stable manifest binding QC outputs to input hashes and policy."""
    return QcEvidenceManifest(
        document_schema=build_document_schema("qc_evidence_manifest"),
        run_id=run_report.run_id,
        batch_id=batch_report.batch_id if batch_report else run_report.batch,
        policy_name=policy.policy_name,
        policy_version=policy.version,
        input_files=input_files,
        run_report_sha256=stable_sha256(run_report),
        run_assessment_sha256=stable_sha256(run_assessment),
        batch_report_sha256=None
        if batch_report is None
        else stable_sha256(batch_report),
        batch_assessment_sha256=None
        if batch_assessment is None
        else stable_sha256(batch_assessment),
        benchmark_sha256=None if benchmark is None else stable_sha256(benchmark),
    )


def build_qc_run_bundle_summary(
    *,
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
    evidence_manifest: QcEvidenceManifest,
) -> QcRunBundleSummary:
    """Join run QC, assessment, and evidence metadata into one review summary."""
    manifest_sha256s = {
        "run_report": evidence_manifest.run_report_sha256,
        "run_assessment": evidence_manifest.run_assessment_sha256,
    }
    if evidence_manifest.batch_report_sha256:
        manifest_sha256s["batch_report"] = evidence_manifest.batch_report_sha256
    if evidence_manifest.batch_assessment_sha256:
        manifest_sha256s["batch_assessment"] = evidence_manifest.batch_assessment_sha256
    if evidence_manifest.benchmark_sha256:
        manifest_sha256s["benchmark"] = evidence_manifest.benchmark_sha256
    return QcRunBundleSummary(
        document_schema=build_document_schema("qc_run_bundle_summary"),
        run_id=run_report.run_id,
        sample_id=run_report.sample_id,
        batch_id=evidence_manifest.batch_id or run_report.batch,
        policy_name=run_assessment.policy_name,
        policy_version=run_assessment.policy_version,
        overall_severity=run_assessment.overall_severity,
        qc_status=run_assessment.qc_status,
        blocked=run_assessment.blocked,
        identification_rate=run_report.identification_rate,
        contaminant_psm_fraction=run_report.contaminant_summary.contaminant_psm_fraction,
        quant_observed_fraction=None
        if run_report.quant_summary is None
        else run_report.quant_summary.observed_fraction,
        anomaly_codes=tuple(sorted(entry.code for entry in run_report.run_anomalies)),
        status_reason_codes=tuple(
            sorted({entry.code for entry in run_assessment.status_reasons})
        ),
        evidence_file_roles=tuple(
            sorted(entry.role for entry in evidence_manifest.input_files)
        ),
        evidence_file_paths=tuple(
            sorted(entry.path for entry in evidence_manifest.input_files)
        ),
        manifest_sha256s=manifest_sha256s,
    )


def build_qc_publication_decision(
    *,
    run_assessment: QcRunAssessmentReport,
    batch_assessment: QcBatchAssessmentReport | None = None,
) -> QcPublicationDecision:
    """Refuse publication or promotion when mandatory QC gates fail."""
    blocking_metric_keys = list(run_assessment.enforced_failure_metric_keys)
    advisory_metric_keys = list(run_assessment.advisory_failure_metric_keys)
    if batch_assessment is not None:
        blocking_metric_keys.extend(batch_assessment.enforced_failure_metric_keys)
        advisory_metric_keys.extend(batch_assessment.advisory_failure_metric_keys)
    blocking_metric_keys = sorted(set(blocking_metric_keys))
    advisory_metric_keys = sorted(set(advisory_metric_keys))
    if blocking_metric_keys:
        reason = "mandatory qc gates failed for metrics: " + ", ".join(
            blocking_metric_keys
        )
        return QcPublicationDecision(
            run_id=run_assessment.run_id,
            publish_allowed=False,
            promote_allowed=False,
            blocking_metric_keys=tuple(blocking_metric_keys),
            reason=reason,
            advisory_metric_keys=tuple(advisory_metric_keys),
        )
    return QcPublicationDecision(
        run_id=run_assessment.run_id,
        publish_allowed=True,
        promote_allowed=True,
        blocking_metric_keys=(),
        reason="mandatory qc gates passed",
        advisory_metric_keys=tuple(advisory_metric_keys),
    )


def build_performance_snapshot(
    run_id: str,
    *,
    operations: dict[str, tuple[float, int | None]],
) -> ProteomicsPerformanceSnapshot:
    """Build a stable performance snapshot from named elapsed operations."""
    entries: list[ProteomicsPerformanceOperation] = []
    total_elapsed_seconds = 0.0
    for operation_name, (elapsed_seconds, item_count) in sorted(operations.items()):
        total_elapsed_seconds += elapsed_seconds
        throughput = None
        if item_count is not None and elapsed_seconds > 0:
            throughput = item_count / elapsed_seconds
        entries.append(
            ProteomicsPerformanceOperation(
                operation=operation_name,
                elapsed_seconds=elapsed_seconds,
                item_count=item_count,
                throughput_per_second=throughput,
            )
        )
    return ProteomicsPerformanceSnapshot(
        document_schema=build_document_schema("proteomics_performance_snapshot"),
        run_id=run_id,
        operations=tuple(entries),
        total_elapsed_seconds=total_elapsed_seconds,
    )


def render_qc_assessment_tsv(
    run_assessment: QcRunAssessmentReport,
    *,
    batch_assessment: QcBatchAssessmentReport | None = None,
) -> str:
    """Render QC assessment rows as a TSV string."""
    rows = [
        [
            "scope",
            "entity_id",
            "qc_status",
            "status_reason_codes",
            "metric_key",
            "metric_label",
            "observed_value",
            "unit",
            "severity",
            "disposition",
            "enforced_violation",
            "message",
        ]
    ]
    for assessment in run_assessment.metric_assessments:
        rows.append(
            [
                "run",
                run_assessment.run_id,
                run_assessment.qc_status.value,
                ";".join(reason.code for reason in run_assessment.status_reasons),
                assessment.metric_key,
                assessment.metric_label,
                format_metric_value(assessment.observed_value),
                assessment.unit or "",
                assessment.severity.value,
                assessment.disposition.value,
                "true" if assessment.enforced_violation else "false",
                assessment.message,
            ]
        )
    if batch_assessment is not None:
        entity_id = batch_assessment.batch_id or "batch"
        for assessment in batch_assessment.metric_assessments:
            rows.append(
                [
                    "batch",
                    entity_id,
                    batch_assessment.qc_status.value,
                    ";".join(reason.code for reason in batch_assessment.status_reasons),
                    assessment.metric_key,
                    assessment.metric_label,
                    format_metric_value(assessment.observed_value),
                    assessment.unit or "",
                    assessment.severity.value,
                    assessment.disposition.value,
                    "true" if assessment.enforced_violation else "false",
                    assessment.message,
                ]
            )
    return "\n".join("\t".join(row) for row in rows) + "\n"


def render_qc_assessment_html(
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
    *,
    batch_report: InstrumentBatchQcReport | None = None,
    batch_assessment: QcBatchAssessmentReport | None = None,
) -> str:
    """Render a compact static HTML QC report."""
    rows = []
    for assessment in run_assessment.metric_assessments:
        rows.append(
            "<tr>"
            f"<td>run</td><td>{run_assessment.run_id}</td><td>{run_assessment.qc_status.value}</td><td>{'; '.join(reason.code for reason in run_assessment.status_reasons) or 'none'}</td><td>{assessment.metric_label}</td>"
            f"<td>{format_metric_value(assessment.observed_value)}</td>"
            f"<td>{assessment.severity.value}</td><td>{assessment.disposition.value}</td><td>{assessment.message}</td>"
            "</tr>"
        )
    if batch_assessment is not None:
        entity_id = batch_assessment.batch_id or "batch"
        for assessment in batch_assessment.metric_assessments:
            rows.append(
                "<tr>"
                f"<td>batch</td><td>{entity_id}</td><td>{batch_assessment.qc_status.value}</td><td>{'; '.join(reason.code for reason in batch_assessment.status_reasons) or 'none'}</td><td>{assessment.metric_label}</td>"
                f"<td>{format_metric_value(assessment.observed_value)}</td>"
                f"<td>{assessment.severity.value}</td><td>{assessment.disposition.value}</td><td>{assessment.message}</td>"
                "</tr>"
            )
    batch_summary = ""
    if batch_report is not None:
        batch_summary = (
            f"<p><strong>Batch</strong>: {batch_report.batch_id or 'n/a'} | "
            f"<strong>Instrument</strong>: {batch_report.instrument or 'n/a'} | "
            f"<strong>Outliers</strong>: {', '.join(batch_report.outlier_run_ids) or 'none'}</p>"
        )
    return (
        "<html><head><title>Bijux Proteomics QC Report</title></head><body>"
        f"<h1>QC report for {run_report.run_id}</h1>"
        f"<p><strong>Sample</strong>: {run_report.sample_id or 'n/a'} | "
        f"<strong>Overall</strong>: {run_assessment.overall_severity.value} | "
        f"<strong>Status</strong>: {run_assessment.qc_status.value} | "
        f"<strong>Blocked</strong>: {'yes' if run_assessment.blocked else 'no'}</p>"
        f"{batch_summary}"
        "<table border='1' cellspacing='0' cellpadding='4'>"
        "<thead><tr><th>Scope</th><th>Entity</th><th>Status</th><th>Reason codes</th><th>Metric</th><th>Observed</th><th>Severity</th><th>Disposition</th><th>Message</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "</body></html>\n"
    )


__all__ = [
    "build_performance_snapshot",
    "build_qc_evidence_manifest",
    "build_qc_publication_decision",
    "build_qc_run_bundle_summary",
    "render_qc_assessment_html",
    "render_qc_assessment_tsv",
]
