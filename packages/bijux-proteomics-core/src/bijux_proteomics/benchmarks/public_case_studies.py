# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned public case-study definitions for end-to-end biological workflow proof."""

from __future__ import annotations

from pathlib import Path
import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import build_biological_result_report_bundle
from bijux_proteomics.workflow.biological_reporting import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
    BiologicalResultSelectionPolicy,
    write_biological_result_report_bundle,
)
from bijux_proteomics_foundation import JsonModel

_CASE_STUDY_ROOT = "packages/bijux-proteomics-core/benchmark-assets/public-case-studies"
_LFQ_CASE_STUDY_ROOT = f"{_CASE_STUDY_ROOT}/lfq_cohort_biological_case_study"
_LFQ_PUBLIC_PACKAGE_ROOT = (
    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
    "lfq_cohort_review_package"
)


class PublicCaseStudyInputPaths(JsonModel):
    """Stable input paths for one public case study."""

    model_config = ConfigDict(extra="forbid")

    feature_table_path: str = Field(..., min_length=1)
    design_table_path: str = Field(..., min_length=1)
    proteins_fasta_path: str = Field(..., min_length=1)
    annotation_tsv_path: str = Field(..., min_length=1)
    go_annotation_tsv_path: str = Field(..., min_length=1)
    pathway_membership_tsv_path: str = Field(..., min_length=1)
    complex_membership_tsv_path: str = Field(..., min_length=1)


class PublicBiologicalCaseStudyDefinition(JsonModel):
    """Owned description of one public dataset case study."""

    model_config = ConfigDict(extra="forbid")

    case_study_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    source_package_id: str = Field(..., min_length=1)
    public_dataset_identity: str = Field(..., min_length=1)
    case_study_root: str = Field(..., min_length=1)
    readme_path: str = Field(..., min_length=1)
    input_paths: PublicCaseStudyInputPaths
    note: str = Field(..., min_length=1)


class PublicBiologicalCaseStudyCatalog(JsonModel):
    """Catalog of owned public dataset case studies."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PublicBiologicalCaseStudyDefinition, ...] = Field(
        default_factory=tuple
    )


class PublicBiologicalCaseStudyReportSummary(JsonModel):
    """Compact summary over one public biological case study run."""

    model_config = ConfigDict(extra="forbid")

    case_study_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    protein_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    go_enriched_term_count: int = Field(..., ge=0)
    pathway_enriched_entry_count: int = Field(..., ge=0)
    complex_enriched_entry_count: int = Field(..., ge=0)


class PublicBiologicalCaseStudyReport(JsonModel):
    """Owned end-to-end report for one public biological case study."""

    model_config = ConfigDict(extra="forbid")

    case_study: PublicBiologicalCaseStudyDefinition
    biological_report: BiologicalResultReportBundle
    selection_policy: BiologicalResultSelectionPolicy
    summary: PublicBiologicalCaseStudyReportSummary
    note: str = Field(..., min_length=1)


class PublicBiologicalCaseStudyArtifactPaths(JsonModel):
    """Relative artifact paths written for one exported public case study."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    biological_report_dir: str = Field(..., min_length=1)
    biological_report_manifest_json: str = Field(..., min_length=1)


class PublicBiologicalCaseStudyExportManifest(JsonModel):
    """Stable manifest over one exported public case-study directory."""

    model_config = ConfigDict(extra="forbid")

    summary: PublicBiologicalCaseStudyReportSummary
    artifacts: PublicBiologicalCaseStudyArtifactPaths
    biological_report_manifest: BiologicalResultReportExportManifest
    note: str = Field(..., min_length=1)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _repo_path(repo_relative_path: str) -> Path:
    return _repo_root() / repo_relative_path


def _readme_path(case_study_root: str) -> str:
    return f"{case_study_root}/README.md"


def _lfq_case_study_input_paths() -> PublicCaseStudyInputPaths:
    return PublicCaseStudyInputPaths(
        feature_table_path=(
            f"{_LFQ_PUBLIC_PACKAGE_ROOT}/evidence/study_scale_ms1_features.tsv"
        ),
        design_table_path=f"{_LFQ_PUBLIC_PACKAGE_ROOT}/evidence/study_scale.design.tsv",
        proteins_fasta_path=f"{_LFQ_CASE_STUDY_ROOT}/biology/reference.fasta",
        annotation_tsv_path=f"{_LFQ_CASE_STUDY_ROOT}/biology/annotations.tsv",
        go_annotation_tsv_path=f"{_LFQ_CASE_STUDY_ROOT}/biology/go_annotations.tsv",
        pathway_membership_tsv_path=(
            f"{_LFQ_CASE_STUDY_ROOT}/biology/pathway_memberships.tsv"
        ),
        complex_membership_tsv_path=(
            f"{_LFQ_CASE_STUDY_ROOT}/biology/complex_memberships.tsv"
        ),
    )


def build_lfq_cohort_biological_case_study() -> PublicBiologicalCaseStudyDefinition:
    """Return the owned public LFQ case study that ends in biological reporting."""

    case_study = PublicBiologicalCaseStudyDefinition(
        case_study_id="public_case_study:lfq_cohort_biological_case_study",
        workflow_family="lfq",
        source_package_id="flagship_public_package:lfq_cohort_review_package",
        public_dataset_identity=(
            "tracked study-scale LFQ feature and cohort-design snapshot promoted to "
            "one bounded biological interpretation case study"
        ),
        case_study_root=_LFQ_CASE_STUDY_ROOT,
        readme_path=_readme_path(_LFQ_CASE_STUDY_ROOT),
        input_paths=_lfq_case_study_input_paths(),
        note=(
            "the LFQ cohort case study reuses the flagship public LFQ package as its "
            "data and sample-metadata substrate, then adds explicit reference and "
            "interpretation memberships so one bounded end-to-end biological report "
            "stays inspectable inside one owned proof surface"
        ),
    )
    _validate_case_study_paths(case_study)
    return case_study


def build_public_biological_case_study_catalog() -> PublicBiologicalCaseStudyCatalog:
    """Return the catalog of owned public biological case studies."""

    return PublicBiologicalCaseStudyCatalog(
        entries=(build_lfq_cohort_biological_case_study(),)
    )


def build_lfq_cohort_biological_case_study_report() -> PublicBiologicalCaseStudyReport:
    """Run the owned LFQ cohort public case study into a final biology bundle."""

    case_study = build_lfq_cohort_biological_case_study()
    selection_policy = BiologicalResultSelectionPolicy(
        max_adjusted_p_value=1.0,
        min_absolute_log2_fold_change=0.1,
        heatmap_max_entity_count=10,
        heatmap_min_observed_fraction=0.5,
    )
    design_entries = tuple(
        parse_experimental_design_table(
            _repo_path(case_study.input_paths.design_table_path)
        ).accepted_entries
    )
    biological_report = build_biological_result_report_bundle(
        _repo_path(case_study.input_paths.feature_table_path),
        design_entries,
        proteins_fasta_path=_repo_path(case_study.input_paths.proteins_fasta_path),
        annotation_tsv_path=_repo_path(case_study.input_paths.annotation_tsv_path),
        go_annotation_tsv_path=_repo_path(case_study.input_paths.go_annotation_tsv_path),
        pathway_membership_tsv_path=_repo_path(
            case_study.input_paths.pathway_membership_tsv_path
        ),
        complex_membership_tsv_path=_repo_path(
            case_study.input_paths.complex_membership_tsv_path
        ),
        condition_a="control",
        condition_b="treatment",
        selection_policy=selection_policy,
    )
    return PublicBiologicalCaseStudyReport(
        case_study=case_study,
        biological_report=biological_report,
        selection_policy=selection_policy,
        summary=PublicBiologicalCaseStudyReportSummary(
            case_study_id=case_study.case_study_id,
            workflow_family=case_study.workflow_family,
            condition_a="control",
            condition_b="treatment",
            protein_count=biological_report.summary.protein_count,
            significant_protein_count=biological_report.summary.significant_protein_count,
            sample_count=biological_report.summary.sample_count,
            go_enriched_term_count=biological_report.summary.go_enriched_term_count,
            pathway_enriched_entry_count=(
                biological_report.summary.pathway_enriched_entry_count
            ),
            complex_enriched_entry_count=(
                biological_report.summary.complex_enriched_entry_count
            ),
        ),
        note=(
            "the LFQ cohort public case study preserves the public feature snapshot, "
            "sample metadata, exploratory effect-size policy, protein differential "
            "output, sample QC, enrichment ledgers, and final biological report in "
            "one owned workflow surface"
        ),
    )


def render_public_biological_case_study_summary_tsv(
    report: PublicBiologicalCaseStudyReport,
) -> str:
    """Render one public biological case-study summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("case_study_id", report.summary.case_study_id))
    writer.writerow(("workflow_family", report.summary.workflow_family))
    writer.writerow(("source_package_id", report.case_study.source_package_id))
    writer.writerow(("condition_a", report.summary.condition_a))
    writer.writerow(("condition_b", report.summary.condition_b))
    writer.writerow(("protein_count", report.summary.protein_count))
    writer.writerow(
        ("significant_protein_count", report.summary.significant_protein_count)
    )
    writer.writerow(("sample_count", report.summary.sample_count))
    writer.writerow(("go_enriched_term_count", report.summary.go_enriched_term_count))
    writer.writerow(
        (
            "pathway_enriched_entry_count",
            report.summary.pathway_enriched_entry_count,
        )
    )
    writer.writerow(
        (
            "complex_enriched_entry_count",
            report.summary.complex_enriched_entry_count,
        )
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def write_public_biological_case_study_bundle(
    report: PublicBiologicalCaseStudyReport,
    output_dir: Path,
) -> PublicBiologicalCaseStudyExportManifest:
    """Write one public biological case study into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "public_case_study_summary.tsv"
    biological_dir_name = "biological-report"
    biological_manifest_name = "biological_report_manifest.json"
    (output_dir / summary_name).write_text(
        render_public_biological_case_study_summary_tsv(report),
        encoding="utf-8",
    )
    biological_dir = output_dir / biological_dir_name
    biological_manifest = write_biological_result_report_bundle(
        report.biological_report,
        biological_dir,
    )
    (biological_dir / biological_manifest_name).write_text(
        biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    return PublicBiologicalCaseStudyExportManifest(
        summary=report.summary,
        artifacts=PublicBiologicalCaseStudyArtifactPaths(
            summary_tsv=summary_name,
            biological_report_dir=biological_dir_name,
            biological_report_manifest_json=(
                f"{biological_dir_name}/{biological_manifest_name}"
            ),
        ),
        biological_report_manifest=biological_manifest,
        note=(
            "public biological case study export preserves a compact case-study "
            "summary alongside the full downstream biological report directory"
        ),
    )


def export_public_biological_case_study_report(
    report: PublicBiologicalCaseStudyReport,
    output_dir: Path,
) -> PublicBiologicalCaseStudyExportManifest:
    """Compatibility wrapper for the legacy public case-study export name."""

    return write_public_biological_case_study_bundle(report, output_dir)


def _validate_case_study_paths(case_study: PublicBiologicalCaseStudyDefinition) -> None:
    required_paths = (
        case_study.readme_path,
        case_study.input_paths.feature_table_path,
        case_study.input_paths.design_table_path,
        case_study.input_paths.proteins_fasta_path,
        case_study.input_paths.annotation_tsv_path,
        case_study.input_paths.go_annotation_tsv_path,
        case_study.input_paths.pathway_membership_tsv_path,
        case_study.input_paths.complex_membership_tsv_path,
    )
    missing = tuple(
        path for path in required_paths if not _repo_path(path).is_file()
    )
    if missing:
        raise FileNotFoundError(
            "public case study is missing required assets: " + ", ".join(missing)
        )


__all__ = [
    "PublicBiologicalCaseStudyCatalog",
    "PublicBiologicalCaseStudyDefinition",
    "PublicBiologicalCaseStudyExportManifest",
    "PublicBiologicalCaseStudyReport",
    "PublicBiologicalCaseStudyArtifactPaths",
    "PublicBiologicalCaseStudyReportSummary",
    "PublicCaseStudyInputPaths",
    "build_lfq_cohort_biological_case_study",
    "build_lfq_cohort_biological_case_study_report",
    "build_public_biological_case_study_catalog",
    "export_public_biological_case_study_report",
    "write_public_biological_case_study_bundle",
    "render_public_biological_case_study_summary_tsv",
]
