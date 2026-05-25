# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Conformance and provenance review over search-adapter normalization runs."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.contracts import (
    TargetDecoyLabel,
    build_calibration_plot_data,
    build_fdr_audit_trail,
    normalize_psm_records,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterConformanceCheck,
    SearchAdapterConformanceReport,
    SearchAdapterNormalizationReport,
    SearchAdapterProvenanceManifest,
)
from bijux_proteomics.identification.search_adapters.input_review import _hash_file, build_search_adapter_field_accounting
from bijux_proteomics.identification.search_adapters.parameter_review import parse_search_parameter_file, supports_search_parameter_parsing
from bijux_proteomics.identification.search_adapters.normalization import _build_parse_provenance
from bijux_proteomics_foundation import DocumentSchema


def build_search_adapter_conformance_report(
    normalization_report: SearchAdapterNormalizationReport,
) -> SearchAdapterConformanceReport:
    """Build a stable conformance report over one adapter normalization run."""
    manifest = normalization_report.adapter_manifest
    field_accounting = build_search_adapter_field_accounting(normalization_report)
    rejection_issue_counts: dict[str, int] = {}
    for rejected in normalization_report.parse_report.rejected_rows:
        for issue in rejected.issues:
            rejection_issue_counts[issue.code] = (
                rejection_issue_counts.get(issue.code, 0) + 1
            )

    checks = [
        SearchAdapterConformanceCheck(
            code="stable_normalized_order",
            passed=normalization_report.normalized_records
            == normalize_psm_records(normalization_report.normalized_records),
            detail="normalized output order matches the shared stable PSM ordering",
        ),
        SearchAdapterConformanceCheck(
            code="q_value_contract",
            passed=(
                not manifest.supports_q_value
                or all(
                    record.q_value is not None
                    for record in normalization_report.normalized_records
                )
            ),
            detail="q-value-supporting adapters must emit q-values for accepted records",
        ),
        SearchAdapterConformanceCheck(
            code="explicit_decoy_contract",
            passed=(
                not manifest.supports_explicit_decoy_label
                or all(
                    record.target_decoy_label is not TargetDecoyLabel.UNKNOWN
                    for record in normalization_report.normalized_records
                )
            ),
            detail="explicit-decoy adapters must not leave accepted rows with unknown labels",
        ),
        SearchAdapterConformanceCheck(
            code="protein_reference_contract",
            passed=(
                not manifest.supports_protein_refs
                or all(
                    record.protein_refs
                    for record in normalization_report.normalized_records
                )
            ),
            detail="protein-aware adapters must emit at least one protein reference per accepted row",
        ),
        SearchAdapterConformanceCheck(
            code="rejected_invalid_score_rows",
            passed=rejection_issue_counts.get("invalid_score", 0) == 0,
            detail="adapter input should not contain invalid score rows for conformance-grade fixtures",
        ),
        SearchAdapterConformanceCheck(
            code="rejected_invalid_q_value_rows",
            passed=rejection_issue_counts.get("invalid_q_value", 0) == 0,
            detail="adapter input should not contain invalid q-value rows for conformance-grade fixtures",
        ),
        SearchAdapterConformanceCheck(
            code="expected_native_fields_present",
            passed=not field_accounting.lost_columns,
            detail="adapter-declared native columns should be present in conformance-grade source tables",
        ),
    ]
    fdr_audit_trail = build_fdr_audit_trail(
        normalization_report.normalized_records,
        score_orientation=manifest.score_orientation.value,
    )
    calibration_plot = build_calibration_plot_data(
        normalization_report.normalized_records,
        score_orientation=manifest.score_orientation.value,
    )
    return SearchAdapterConformanceReport(
        adapter_kind=manifest.adapter_kind,
        accepted_rows=len(normalization_report.parse_report.accepted_records),
        rejected_rows=len(normalization_report.parse_report.rejected_rows),
        rejection_issue_counts=dict(sorted(rejection_issue_counts.items())),
        field_accounting=field_accounting,
        checks=tuple(checks),
        passes=all(check.passed for check in checks),
        fdr_audit_trail=fdr_audit_trail,
        calibration_plot=calibration_plot,
    )


def build_search_adapter_provenance_manifest(
    *,
    source_path: Path,
    normalization_report: SearchAdapterNormalizationReport,
    adapter_version: str | None = None,
    config_path: Path | None = None,
) -> SearchAdapterProvenanceManifest:
    """Build provenance for one adapter normalization pass."""
    parameter_report = (
        parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=normalization_report.adapter_manifest.adapter_kind,
        )
        if config_path is not None
        and supports_search_parameter_parsing(
            normalization_report.adapter_manifest.adapter_kind
        )
        else None
    )
    parse_provenance = _build_parse_provenance(
        source_path=source_path,
        parse_report=normalization_report.parse_report,
        adapter_manifest=normalization_report.adapter_manifest,
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_adapter_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchAdapterProvenanceManifest(
        document_schema=schema,
        adapter_kind=normalization_report.adapter_manifest.adapter_kind,
        adapter_name=normalization_report.adapter_manifest.display_name,
        adapter_version=adapter_version,
        source_path=str(source_path),
        source_sha256=_hash_file(source_path) or "",
        config_path=str(config_path) if config_path is not None else None,
        config_sha256=_hash_file(config_path),
        parameter_report=parameter_report,
        result_family=normalization_report.adapter_manifest.result_family,
        family_policy=normalization_report.family_policy,
        native_columns=normalization_report.adapter_manifest.native_columns,
        score_orientation=normalization_report.adapter_manifest.score_orientation,
        parse_provenance=parse_provenance,
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )
