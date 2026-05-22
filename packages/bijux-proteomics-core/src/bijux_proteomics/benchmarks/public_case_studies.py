# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned public case-study definitions for end-to-end biological workflow proof."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

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
    "PublicCaseStudyInputPaths",
    "build_lfq_cohort_biological_case_study",
    "build_public_biological_case_study_catalog",
]
