# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Durable asset-root contracts for flagship public benchmark packages."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from ipaddress import ip_address
import json
from pathlib import Path
from urllib.parse import SplitResult, urlsplit

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

_FLAGSHIP_ROOT = (
    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages"
)
_ROOT_CONTRACT_PATH = f"{_FLAGSHIP_ROOT}/asset_root_contract.json"
_FRESHNESS_REPORT_PATH = f"{_FLAGSHIP_ROOT}/freshness_report.json"
_OBSOLESCENCE_AUDIT_PATH = f"{_FLAGSHIP_ROOT}/obsolescence_audit.json"
_REFRESH_COMMAND = (
    "uv run --group dev python -m "
    "bijux_proteomics.benchmarks.flagship.maintenance refresh"
)


class FlagshipAssetBoundaryKind(StrEnum):
    """Stable categories for files tracked inside a flagship asset root."""

    COPIED_SNAPSHOT = "copied_snapshot"
    CURATED_METADATA = "curated_metadata"
    CURATED_README = "curated_readme"
    GENERATED_REPORT = "generated_report"


class FlagshipRemoteSource(JsonModel):
    """One public-facing source tied to a flagship asset root."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1)
    public_source_name: str = Field(..., min_length=1)
    local_artifact_path: str = Field(..., min_length=1)
    upstream_repo_source_path: str = Field(..., min_length=1)
    public_reference_url: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)
    availability_expectation: str = Field(..., min_length=1)
    license_note: str = Field(..., min_length=1)


class FlagshipCitationReference(JsonModel):
    """One citation that justifies part of a flagship asset root."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    doi: str | None = None
    url: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)


class FlagshipGeneratedBoundaryRecord(JsonModel):
    """Explain whether a tracked file is copied, curated, or generated."""

    model_config = ConfigDict(extra="forbid")

    artifact_path: str = Field(..., min_length=1)
    boundary_kind: FlagshipAssetBoundaryKind
    regeneration_command: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FlagshipAssetRootEntry(JsonModel):
    """One durable asset-root contract entry for a flagship package."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    asset_root: str = Field(..., min_length=1)
    source_locator_manifest_path: str = Field(..., min_length=1)
    citation_manifest_path: str = Field(..., min_length=1)
    generated_boundary_path: str = Field(..., min_length=1)
    rebuild_instructions_path: str = Field(..., min_length=1)
    expected_wall_time_minutes: int = Field(..., ge=1)
    expected_disk_footprint_mb: int = Field(..., ge=1)
    known_license_limits: tuple[str, ...] = Field(default_factory=tuple)
    remote_sources: tuple[FlagshipRemoteSource, ...] = Field(default_factory=tuple)
    citations: tuple[FlagshipCitationReference, ...] = Field(default_factory=tuple)
    generated_boundaries: tuple[FlagshipGeneratedBoundaryRecord, ...] = Field(
        default_factory=tuple
    )


class FlagshipAssetRootContract(JsonModel):
    """Repository-wide contract for flagship public benchmark asset roots."""

    model_config = ConfigDict(extra="forbid")

    contract_id: str = Field(..., min_length=1)
    contract_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipAssetRootEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipRemoteAvailabilityStatus(StrEnum):
    """Outcome of one remote availability probe."""

    AVAILABLE = "available"
    HTTP_ERROR = "http_error"
    NETWORK_ERROR = "network_error"
    INVALID_URL = "invalid_url"


class FlagshipRemoteAvailabilityCheck(JsonModel):
    """One live or simulated remote availability result."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1)
    public_reference_url: str = Field(..., min_length=1)
    status: FlagshipRemoteAvailabilityStatus
    detail: str = Field(..., min_length=1)


class FlagshipAssetFreshnessEntry(JsonModel):
    """Freshness state for one flagship asset root."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    asset_root: str = Field(..., min_length=1)
    local_paths_present: bool
    local_path_count: int = Field(..., ge=0)
    remote_checks: tuple[FlagshipRemoteAvailabilityCheck, ...] = Field(
        default_factory=tuple
    )
    citation_count: int = Field(..., ge=0)
    freshness_state: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FlagshipAssetRefreshReport(JsonModel):
    """Output of a flagship asset refresh check."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    report_path: str = Field(..., min_length=1)
    checked_on: datetime
    entries: tuple[FlagshipAssetFreshnessEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipAssetObsolescenceEntry(JsonModel):
    """One public package obsolescence audit row."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    stronger_public_dataset_needed: bool
    stronger_public_dataset_reason: str = Field(..., min_length=1)
    replacement_direction: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FlagshipAssetObsolescenceAudit(JsonModel):
    """Cross-family obsolescence pressure for flagship asset roots."""

    model_config = ConfigDict(extra="forbid")

    audit_id: str = Field(..., min_length=1)
    audit_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipAssetObsolescenceEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def flagship_asset_root(package_dir_name: str) -> str:
    """Return the durable product-owned asset root for one flagship package."""

    return f"{_FLAGSHIP_ROOT}/{package_dir_name}"


def flagship_asset_contract_path() -> str:
    """Return the checked shared asset-root contract path."""

    return _ROOT_CONTRACT_PATH


def flagship_asset_refresh_report_path() -> str:
    """Return the checked freshness report path."""

    return _FRESHNESS_REPORT_PATH


def flagship_asset_obsolescence_audit_path() -> str:
    """Return the checked obsolescence audit path."""

    return _OBSOLESCENCE_AUDIT_PATH


def _source_locator_manifest_path(package_dir_name: str) -> str:
    return f"{flagship_asset_root(package_dir_name)}/source_locator_manifest.json"


def _citation_manifest_path(package_dir_name: str) -> str:
    return f"{flagship_asset_root(package_dir_name)}/citation_manifest.json"


def _generated_boundary_path(package_dir_name: str) -> str:
    return f"{flagship_asset_root(package_dir_name)}/generated_boundary.json"


def _rebuild_instructions_path(package_dir_name: str) -> str:
    return f"{flagship_asset_root(package_dir_name)}/rebuild_instructions.md"


def _remote_source(
    *,
    source_id: str,
    public_source_name: str,
    package_dir_name: str,
    local_relative: str,
    upstream_repo_source_path: str,
    public_reference_url: str,
    why_it_matters: str,
    availability_expectation: str,
    license_note: str,
) -> FlagshipRemoteSource:
    return FlagshipRemoteSource(
        source_id=source_id,
        public_source_name=public_source_name,
        local_artifact_path=f"{flagship_asset_root(package_dir_name)}/{local_relative}",
        upstream_repo_source_path=upstream_repo_source_path,
        public_reference_url=public_reference_url,
        why_it_matters=why_it_matters,
        availability_expectation=availability_expectation,
        license_note=license_note,
    )


def _citation(
    *,
    citation_id: str,
    title: str,
    url: str,
    why_it_matters: str,
    doi: str | None = None,
) -> FlagshipCitationReference:
    return FlagshipCitationReference(
        citation_id=citation_id,
        title=title,
        doi=doi,
        url=url,
        why_it_matters=why_it_matters,
    )


def _boundary(
    *,
    package_dir_name: str,
    artifact_relative: str,
    boundary_kind: FlagshipAssetBoundaryKind,
    regeneration_command: str,
    note: str,
) -> FlagshipGeneratedBoundaryRecord:
    return FlagshipGeneratedBoundaryRecord(
        artifact_path=f"{flagship_asset_root(package_dir_name)}/{artifact_relative}",
        boundary_kind=boundary_kind,
        regeneration_command=regeneration_command,
        note=note,
    )


def _asset_root_entries() -> tuple[FlagshipAssetRootEntry, ...]:
    return (
        FlagshipAssetRootEntry(
            package_id="flagship_public_package:dda_reviewable_run",
            workflow_family="dda",
            asset_root=flagship_asset_root("dda_reviewable_run"),
            source_locator_manifest_path=_source_locator_manifest_path(
                "dda_reviewable_run"
            ),
            citation_manifest_path=_citation_manifest_path("dda_reviewable_run"),
            generated_boundary_path=_generated_boundary_path("dda_reviewable_run"),
            rebuild_instructions_path=_rebuild_instructions_path("dda_reviewable_run"),
            expected_wall_time_minutes=6,
            expected_disk_footprint_mb=8,
            known_license_limits=(
                "The tracked DDA package currently ships checked exported-result snapshots, not live MaxQuant or MSFragger executables.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="dda:maxquant_reference",
                    public_source_name="MaxQuant DDA export snapshot",
                    package_dir_name="dda_reviewable_run",
                    local_relative="primary/maxquant_pipeline_export.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv",
                    public_reference_url="https://www.maxquant.org/",
                    why_it_matters="MaxQuant defines the primary imported DDA result dialect for the current flagship package.",
                    availability_expectation="The MaxQuant project page should remain reachable while the imported-result dialect stays part of flagship DDA proof.",
                    license_note="The local file is a tracked snapshot; public availability check targets the project source page, not a downloadable binary.",
                ),
                _remote_source(
                    source_id="dda:msfragger_reference",
                    public_source_name="MSFragger comparator export snapshot",
                    package_dir_name="dda_reviewable_run",
                    local_relative="comparator/msfragger_pipeline_export.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv",
                    public_reference_url="https://msfragger.nesvilab.org/",
                    why_it_matters="MSFragger defines the comparator dialect used for the flagship DDA cross-engine warning surface.",
                    availability_expectation="The MSFragger project page should remain reachable while comparator-backed DDA proof depends on it.",
                    license_note="The local file is a tracked snapshot; public availability check targets the project source page, not an executable redistribution path.",
                ),
                _remote_source(
                    source_id="dda:reference_proteome",
                    public_source_name="UniProt reference proteome design context",
                    package_dir_name="dda_reviewable_run",
                    local_relative="evidence/design.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/production_run/design.tsv",
                    public_reference_url="https://www.uniprot.org",
                    why_it_matters="The DDA package relies on reference proteome context to keep peptide and protein review grounded.",
                    availability_expectation="UniProt should remain reachable while the reference grounding claim stays in force.",
                    license_note="Public availability check targets the reference resource page used by the package README and citation manifest.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:target_decoy_2007",
                    title="Significance analysis of shotgun proteomics data",
                    doi="10.1038/nmeth1019",
                    url="https://www.nature.com/articles/nmeth1019",
                    why_it_matters="Anchors target-decoy caution in the flagship DDA package.",
                ),
                _citation(
                    citation_id="citation:protein_inference_2012",
                    title="Computational solutions for mass spectrometry-based protein inference",
                    doi="10.1074/mcp.R111.014795",
                    url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3494198/",
                    why_it_matters="Anchors protein-inference caution in the flagship DDA package.",
                ),
                _citation(
                    citation_id="citation:uniprot_2025",
                    title="UniProt: the Universal Protein Knowledgebase in 2025",
                    doi="10.1093/nar/gkae1010",
                    url="https://www.uniprot.org",
                    why_it_matters="Anchors the reference proteome context named in the package.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_dir_name="dda_reviewable_run",
                    artifact_relative="evidence/spectra.mgf",
                    boundary_kind=FlagshipAssetBoundaryKind.COPIED_SNAPSHOT,
                    regeneration_command="rsync the tracked spectrum snapshot from tests/fixtures into the flagship asset root",
                    note="The raw-like spectrum is copied from the legacy fixture source so the flagship package can own a stable local evidence copy.",
                ),
                _boundary(
                    package_dir_name="dda_reviewable_run",
                    artifact_relative="package_manifest.json",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    regeneration_command=_REFRESH_COMMAND,
                    note="The package manifest is generated from code-owned benchmark and asset-root builders.",
                ),
                _boundary(
                    package_dir_name="dda_reviewable_run",
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    regeneration_command="edit the README when flagship DDA authority changes and rerun the asset maintenance refresh",
                    note="The README is human-curated because it explains authority and limits in outsider-facing language.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="flagship_public_package:dia_library_review_package",
            workflow_family="dia",
            asset_root=flagship_asset_root("dia_library_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                "dia_library_review_package"
            ),
            citation_manifest_path=_citation_manifest_path(
                "dia_library_review_package"
            ),
            generated_boundary_path=_generated_boundary_path(
                "dia_library_review_package"
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                "dia_library_review_package"
            ),
            expected_wall_time_minutes=7,
            expected_disk_footprint_mb=8,
            known_license_limits=(
                "The DIA package currently ships imported report snapshots and settings, not live vendor chromatogram execution.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="dia:spectronaut_reference",
                    public_source_name="Spectronaut DIA report snapshot",
                    package_dir_name="dia_library_review_package",
                    local_relative="primary/spectronaut_report.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv",
                    public_reference_url="https://biognosys.com/software/spectronaut/",
                    why_it_matters="Spectronaut defines the primary library-conditioned DIA evidence dialect carried by the flagship package.",
                    availability_expectation="The Spectronaut product page should remain reachable while the package stays anchored to this import surface.",
                    license_note="The local file is a tracked snapshot; public availability check targets the product reference page.",
                ),
                _remote_source(
                    source_id="dia:diann_reference",
                    public_source_name="DIA-NN comparator export snapshot",
                    package_dir_name="dia_library_review_package",
                    local_relative="comparator/diann_pipeline_export.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv",
                    public_reference_url="https://github.com/vdemichev/DiaNN",
                    why_it_matters="DIA-NN defines the comparator dialect used in the flagship DIA confrontation.",
                    availability_expectation="The DIA-NN project page should remain reachable while confrontation-backed DIA proof depends on it.",
                    license_note="The local file is a tracked snapshot; public availability check targets the public project page.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:diann_2020",
                    title="DIA-NN: neural networks and interference correction enable deep proteome coverage in high throughput",
                    doi="10.1038/s41592-019-0638-x",
                    url="https://www.nature.com/articles/s41592-019-0638-x",
                    why_it_matters="Anchors the DIA-NN comparator dialect in the flagship DIA package.",
                ),
                _citation(
                    citation_id="citation:dia_library_limits",
                    title="Library-based data-independent acquisition still carries library completeness assumptions",
                    url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6949130/",
                    why_it_matters="Anchors the library-conditioned caution in the flagship DIA package.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_dir_name="dia_library_review_package",
                    artifact_relative="package_manifest.json",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    regeneration_command=_REFRESH_COMMAND,
                    note="The DIA package manifest is generated from shared builders.",
                ),
                _boundary(
                    package_dir_name="dia_library_review_package",
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    regeneration_command="edit the README when the DIA authority boundary changes and rerun the asset maintenance refresh",
                    note="The README is curated because it names library-conditioned limits in outsider-facing language.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="flagship_public_package:lfq_cohort_review_package",
            workflow_family="lfq",
            asset_root=flagship_asset_root("lfq_cohort_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                "lfq_cohort_review_package"
            ),
            citation_manifest_path=_citation_manifest_path("lfq_cohort_review_package"),
            generated_boundary_path=_generated_boundary_path(
                "lfq_cohort_review_package"
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                "lfq_cohort_review_package"
            ),
            expected_wall_time_minutes=5,
            expected_disk_footprint_mb=5,
            known_license_limits=(
                "The LFQ package currently ships cohort-shaped feature and design snapshots, not a second raw cohort or spike-in truth package.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="lfq:normalization_reference",
                    public_source_name="Study-scale LFQ feature table snapshot",
                    package_dir_name="lfq_cohort_review_package",
                    local_relative="evidence/study_scale_ms1_features.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/quant/study_scale_ms1_features.tsv",
                    public_reference_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5862339/",
                    why_it_matters="The flagship LFQ package is judged against cohort-scale missingness and normalization expectations, not toy abundance matrices.",
                    availability_expectation="The public normalization and missingness reference should remain reachable while LFQ authority remains bounded by cohort-shaped evidence.",
                    license_note="The local file is a tracked snapshot; public availability check targets the public methodology reference.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:lfq_missingness_reference",
                    title="Missing value imputation and quantitative reproducibility remain central LFQ trust pressures",
                    url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5862339/",
                    why_it_matters="Anchors the cohort-scale missingness and reproducibility caution in the LFQ package.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_dir_name="lfq_cohort_review_package",
                    artifact_relative="package_manifest.json",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    regeneration_command=_REFRESH_COMMAND,
                    note="The LFQ package manifest is generated from shared builders.",
                ),
                _boundary(
                    package_dir_name="lfq_cohort_review_package",
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    regeneration_command="edit the README when LFQ authority changes and rerun the asset maintenance refresh",
                    note="The README is curated because it explains current LFQ trust boundaries in human language.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="flagship_public_package:multiplex_tmtpro_review_package",
            workflow_family="multiplex",
            asset_root=flagship_asset_root("multiplex_tmtpro_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                "multiplex_tmtpro_review_package"
            ),
            citation_manifest_path=_citation_manifest_path(
                "multiplex_tmtpro_review_package"
            ),
            generated_boundary_path=_generated_boundary_path(
                "multiplex_tmtpro_review_package"
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                "multiplex_tmtpro_review_package"
            ),
            expected_wall_time_minutes=5,
            expected_disk_footprint_mb=4,
            known_license_limits=(
                "The multiplex package currently ships TMTpro-shaped reporter-ion, feature, and design snapshots, not a raw vendor acquisition replay.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="multiplex:tmtpro_reporter_reference",
                    public_source_name="TMTpro reporter-ion table snapshot",
                    package_dir_name="multiplex_tmtpro_review_package",
                    local_relative="evidence/tmt_reporter_table.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/multiplex/maxquant_tmt_interference.tsv",
                    public_reference_url="https://www.thermofisher.com/order/catalog/product/A44520",
                    why_it_matters="The flagship multiplex package is explicitly about TMTpro reporter channels, interference pressure, and reference-channel design.",
                    availability_expectation="The TMTpro product reference should remain reachable while the package stays tied to TMTpro chemistry claims.",
                    license_note="The local file is a tracked snapshot; public availability check targets the chemistry reference page.",
                ),
                _remote_source(
                    source_id="multiplex:feature_snapshot_reference",
                    public_source_name="TMTpro channel-level feature snapshot",
                    package_dir_name="multiplex_tmtpro_review_package",
                    local_relative="evidence/multiplex_ms1_features.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/quant/multiplex_ms1_features.tsv",
                    public_reference_url="https://www.thermofisher.com/order/catalog/product/A44520",
                    why_it_matters="The retained feature snapshot keeps runtime and challenge surfaces tied to the original multiplex intensity view.",
                    availability_expectation="The TMTpro product reference should remain reachable while the package stays tied to TMTpro chemistry claims.",
                    license_note="The local file is a tracked snapshot; public availability check targets the chemistry reference page.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:multiplex_ratio_compression",
                    title="Ratio compression and interference remain central multiplex interpretation pressures",
                    url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5001537/",
                    why_it_matters="Anchors the ratio-compression and interference caution in the multiplex package.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_dir_name="multiplex_tmtpro_review_package",
                    artifact_relative="package_manifest.json",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    regeneration_command=_REFRESH_COMMAND,
                    note="The multiplex package manifest is generated from shared builders.",
                ),
                _boundary(
                    package_dir_name="multiplex_tmtpro_review_package",
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    regeneration_command="edit the README when multiplex authority changes and rerun the asset maintenance refresh",
                    note="The README is curated because it explains chemistry-specific authority and limits.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="flagship_public_package:ptm_localization_review_package",
            workflow_family="ptm",
            asset_root=flagship_asset_root("ptm_localization_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                "ptm_localization_review_package"
            ),
            citation_manifest_path=_citation_manifest_path(
                "ptm_localization_review_package"
            ),
            generated_boundary_path=_generated_boundary_path(
                "ptm_localization_review_package"
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                "ptm_localization_review_package"
            ),
            expected_wall_time_minutes=6,
            expected_disk_footprint_mb=6,
            known_license_limits=(
                "The PTM package currently ships localization and occupancy snapshots, not live rescoring or broad PTM-family execution parity.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="ptm:ascore_reference",
                    public_source_name="PTM localization result snapshot",
                    package_dir_name="ptm_localization_review_package",
                    local_relative="evidence/localization_results.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv",
                    public_reference_url="https://pubmed.ncbi.nlm.nih.gov/16964243/",
                    why_it_matters="The flagship PTM package is judged against localization ambiguity and site-assignment caution.",
                    availability_expectation="The PTM localization reference should remain reachable while localization authority stays central to the package.",
                    license_note="The local file is a tracked snapshot; public availability check targets the PTM-localization reference page.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:ascore_2006",
                    title="AScore: a probability-based tool for evaluating phosphorylation site localization",
                    doi="10.1021/ac060835b",
                    url="https://pubmed.ncbi.nlm.nih.gov/16964243/",
                    why_it_matters="Anchors localization confidence and ambiguity caution in the PTM package.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_dir_name="ptm_localization_review_package",
                    artifact_relative="package_manifest.json",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    regeneration_command=_REFRESH_COMMAND,
                    note="The PTM package manifest is generated from shared builders.",
                ),
                _boundary(
                    package_dir_name="ptm_localization_review_package",
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    regeneration_command="edit the README when PTM authority changes and rerun the asset maintenance refresh",
                    note="The README is curated because it names ambiguity and targetability limits in human language.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="flagship_public_package:targeted_transition_review_package",
            workflow_family="targeted",
            asset_root=flagship_asset_root("targeted_transition_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                "targeted_transition_review_package"
            ),
            citation_manifest_path=_citation_manifest_path(
                "targeted_transition_review_package"
            ),
            generated_boundary_path=_generated_boundary_path(
                "targeted_transition_review_package"
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                "targeted_transition_review_package"
            ),
            expected_wall_time_minutes=5,
            expected_disk_footprint_mb=4,
            known_license_limits=(
                "The targeted package currently ships a runnable Skyline-style result export, design metadata, supporting QC, and consequence packet snapshots, not live vendor chromatogram execution or external calibration reruns.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="targeted:skyline_result_snapshot",
                    public_source_name="Skyline-style targeted result snapshot",
                    package_dir_name="targeted_transition_review_package",
                    local_relative="evidence/skyline_targeted_qc_results.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/formats/skyline_targeted_qc_results.tsv",
                    public_reference_url="https://pubmed.ncbi.nlm.nih.gov/21423193/",
                    why_it_matters="The flagship targeted package now proves matrix and assay-QC regeneration from one runnable Skyline-style transition export.",
                    availability_expectation="The targeted assay guideline reference should remain reachable while targeted authority remains bounded by matrix, QC, and consequence evidence.",
                    license_note="The local file is a tracked snapshot; public availability check targets the targeted-guideline reference page.",
                ),
                _remote_source(
                    source_id="targeted:design_snapshot",
                    public_source_name="Targeted replicate design snapshot",
                    package_dir_name="targeted_transition_review_package",
                    local_relative="evidence/skyline_targeted_qc.design.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/formats/skyline_targeted_qc.design.tsv",
                    public_reference_url="https://pubmed.ncbi.nlm.nih.gov/21423193/",
                    why_it_matters="The targeted design keeps replicate and condition structure explicit for coelution, fragment-ratio, and replicate-CV review.",
                    availability_expectation="The targeted assay guideline reference should remain reachable while targeted authority remains bounded by matrix, QC, and consequence evidence.",
                    license_note="The local file is a tracked snapshot; public availability check targets the targeted-guideline reference page.",
                ),
                _remote_source(
                    source_id="targeted:qc_snapshot",
                    public_source_name="Targeted QC evidence snapshot",
                    package_dir_name="targeted_transition_review_package",
                    local_relative="evidence/targeted_benchmark_qc.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv",
                    public_reference_url="https://pubmed.ncbi.nlm.nih.gov/21423193/",
                    why_it_matters="The flagship targeted package still keeps the older targeted QC ledger visible beside the runnable assay benchmark input.",
                    availability_expectation="The targeted assay guideline reference should remain reachable while targeted authority remains bounded by matrix, QC, and consequence evidence.",
                    license_note="The local file is a tracked snapshot; public availability check targets the targeted-guideline reference page.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:targeted_guideline_2011",
                    title="Guidelines for performing targeted proteomics assays",
                    url="https://pubmed.ncbi.nlm.nih.gov/21423193/",
                    why_it_matters="Anchors transition-level QC and follow-up discipline in the targeted package.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_dir_name="targeted_transition_review_package",
                    artifact_relative="package_manifest.json",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    regeneration_command=_REFRESH_COMMAND,
                    note="The targeted package manifest is generated from shared builders.",
                ),
                _boundary(
                    package_dir_name="targeted_transition_review_package",
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    regeneration_command="edit the README when targeted authority changes and rerun the asset maintenance refresh",
                    note="The README is curated because it explains targeted consequence and calibration limits in human language.",
                ),
            ),
        ),
    )


def list_flagship_asset_root_entries() -> tuple[FlagshipAssetRootEntry, ...]:
    """Return every flagship asset-root contract entry."""

    return _asset_root_entries()


def build_flagship_asset_root_contract() -> FlagshipAssetRootContract:
    """Build the shared flagship asset-root contract."""

    return FlagshipAssetRootContract(
        contract_id="flagship-asset-root-contract",
        contract_path=flagship_asset_contract_path(),
        entries=list_flagship_asset_root_entries(),
        note=(
            "The flagship asset-root contract tells maintainers where each public package lives, how to rebuild it, which copied snapshots it depends on, and what public references keep the package scientifically interpretable."
        ),
    )


def _validated_public_reference(url: str) -> tuple[SplitResult, str]:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("unsupported url scheme")
    if not parsed.netloc or parsed.username is not None or parsed.password is not None:
        raise ValueError("url must have a public host without embedded credentials")
    host = parsed.hostname
    if host is None:
        raise ValueError("url must have a resolvable host")
    try:
        address = ip_address(host)
    except ValueError as exc:
        if host == "localhost" or host.endswith(".local"):
            raise ValueError("url host must be publicly routable") from exc
    else:
        if (
            address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_private
            or address.is_reserved
            or address.is_unspecified
        ):
            raise ValueError("url host must be publicly routable")
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return parsed, path


def _check_remote_url(url: str) -> FlagshipRemoteAvailabilityCheck:
    try:
        parsed, path = _validated_public_reference(url)
    except ValueError:
        status = FlagshipRemoteAvailabilityStatus.INVALID_URL
        detail = "invalid url"
    else:
        connection_cls = HTTPSConnection if parsed.scheme == "https" else HTTPConnection
        connection = connection_cls(parsed.netloc, timeout=10)
        try:
            connection.request(
                "HEAD",
                path,
                headers={"User-Agent": "bijux-proteomics-asset-audit/1.0"},
            )
            response = connection.getresponse()
            detail = f"http {response.status}"
            status = (
                FlagshipRemoteAvailabilityStatus.AVAILABLE
                if 200 <= response.status < 400
                else FlagshipRemoteAvailabilityStatus.HTTP_ERROR
            )
        except HTTPException as exc:  # pragma: no cover - network-dependent branch
            status = FlagshipRemoteAvailabilityStatus.NETWORK_ERROR
            detail = str(exc)
        except OSError as exc:  # pragma: no cover - network-dependent branch
            status = FlagshipRemoteAvailabilityStatus.NETWORK_ERROR
            detail = str(exc)
        finally:
            connection.close()
    return FlagshipRemoteAvailabilityCheck(
        source_id=url,
        public_reference_url=url,
        status=status,
        detail=detail,
    )


def build_flagship_asset_refresh_report(
    *,
    check_remote: bool,
) -> FlagshipAssetRefreshReport:
    """Build the flagship asset freshness report."""

    repo_root = _repo_root()
    entries: list[FlagshipAssetFreshnessEntry] = []
    for entry in list_flagship_asset_root_entries():
        local_paths_present = all(
            (repo_root / source.local_artifact_path).exists()
            for source in entry.remote_sources
        )
        remote_checks_list: list[FlagshipRemoteAvailabilityCheck] = []
        for source in entry.remote_sources:
            if check_remote:
                remote_check = _check_remote_url(source.public_reference_url)
                remote_checks_list.append(
                    FlagshipRemoteAvailabilityCheck(
                        source_id=source.source_id,
                        public_reference_url=source.public_reference_url,
                        status=remote_check.status,
                        detail=remote_check.detail,
                    )
                )
            else:
                remote_checks_list.append(
                    FlagshipRemoteAvailabilityCheck(
                        source_id=source.source_id,
                        public_reference_url=source.public_reference_url,
                        status=FlagshipRemoteAvailabilityStatus.AVAILABLE,
                        detail="remote checks skipped by caller",
                    )
                )
        remote_checks = tuple(remote_checks_list)
        all_remote_available = all(
            check.status is FlagshipRemoteAvailabilityStatus.AVAILABLE
            for check in remote_checks
        )
        freshness_state = (
            "ready"
            if local_paths_present and all_remote_available
            else "attention_required"
        )
        entries.append(
            FlagshipAssetFreshnessEntry(
                package_id=entry.package_id,
                workflow_family=entry.workflow_family,
                asset_root=entry.asset_root,
                local_paths_present=local_paths_present,
                local_path_count=len(entry.remote_sources),
                remote_checks=remote_checks,
                citation_count=len(entry.citations),
                freshness_state=freshness_state,
                note=(
                    "Remote source pages stay reachable and copied snapshots still exist."
                    if freshness_state == "ready"
                    else "At least one copied snapshot or remote reference needs maintainer attention."
                ),
            )
        )
    return FlagshipAssetRefreshReport(
        report_id="flagship-asset-refresh-report",
        report_path=flagship_asset_refresh_report_path(),
        checked_on=datetime.now(UTC),
        entries=tuple(entries),
        note=(
            "The freshness report keeps remote reference availability, copied snapshot presence, and citation count visible before the repository claims stronger flagship authority."
        ),
    )


def build_flagship_asset_obsolescence_audit() -> FlagshipAssetObsolescenceAudit:
    """Build the cross-family obsolescence audit for flagship assets."""

    return FlagshipAssetObsolescenceAudit(
        audit_id="flagship-asset-obsolescence-audit",
        audit_path=flagship_asset_obsolescence_audit_path(),
        entries=(
            FlagshipAssetObsolescenceEntry(
                package_id="flagship_public_package:dda_reviewable_run",
                workflow_family="dda",
                stronger_public_dataset_needed=True,
                stronger_public_dataset_reason="The current DDA package is still one run with imported-result snapshots; broader multi-run or raw-search public proof would be stronger.",
                replacement_direction="Replace the one-run DDA package with a multi-run public DDA asset root that still preserves paired comparator confrontation.",
                note="DDA is strong enough to lead current public proof, but not strong enough to close family-wide generalization.",
            ),
            FlagshipAssetObsolescenceEntry(
                package_id="flagship_public_package:dia_library_review_package",
                workflow_family="dia",
                stronger_public_dataset_needed=True,
                stronger_public_dataset_reason="The current DIA package is still library-conditioned and import-backed; chromatogram- or raw-backed public DIA proof would be stronger.",
                replacement_direction="Replace the import-backed DIA package with a raw-executable or chromatogram-backed DIA asset root.",
                note="DIA remains public and useful, but its current package shape should not be the end state.",
            ),
            FlagshipAssetObsolescenceEntry(
                package_id="flagship_public_package:lfq_cohort_review_package",
                workflow_family="lfq",
                stronger_public_dataset_needed=True,
                stronger_public_dataset_reason="The current LFQ package still lacks second-dataset and stronger truth-surface pressure beyond cohort repeatability.",
                replacement_direction="Replace the current LFQ package with a pair of public cohort packages that expose stronger truth and generalization pressure.",
                note="LFQ package legitimacy improved, but it is still a midpoint asset root.",
            ),
            FlagshipAssetObsolescenceEntry(
                package_id="flagship_public_package:multiplex_tmtpro_review_package",
                workflow_family="multiplex",
                stronger_public_dataset_needed=True,
                stronger_public_dataset_reason="The current multiplex package captures chemistry pressure but still lacks raw-executable and consequence-bearing breadth.",
                replacement_direction="Replace the current TMTpro package with a broader multiplex asset root that includes runtime and follow-up consequence closure.",
                note="Multiplex is still below outsider-auditable standard.",
            ),
            FlagshipAssetObsolescenceEntry(
                package_id="flagship_public_package:ptm_localization_review_package",
                workflow_family="ptm",
                stronger_public_dataset_needed=True,
                stronger_public_dataset_reason="The current PTM package lacks second-family breadth, runtime parity, and comparator-backed decision-grade closure.",
                replacement_direction="Replace the current PTM package with one that broadens PTM-family scope and closes runtime plus comparator gaps.",
                note="PTM package visibility improved, but the package should still be treated as transitional evidence, not final authority.",
            ),
            FlagshipAssetObsolescenceEntry(
                package_id="flagship_public_package:targeted_transition_review_package",
                workflow_family="targeted",
                stronger_public_dataset_needed=True,
                stronger_public_dataset_reason="The current targeted package still centers on QC and consequence packet snapshots without broader raw-executable calibration proof.",
                replacement_direction="Replace the current targeted package with a raw-executable targeted asset root that includes calibration and comparator closure.",
                note="Targeted package is public now, but still materially behind the authority bar implied by a flagship label.",
            ),
        ),
        note=(
            "Every current flagship asset root is useful, but none should be mistaken for the final strongest public benchmark shape for its family."
        ),
    )


def write_flagship_asset_support_files(
    *,
    check_remote: bool,
) -> tuple[str, ...]:
    """Materialize shared asset-root support files into governed package roots."""

    repo_root = _repo_root()
    written: list[str] = []
    contract = build_flagship_asset_root_contract()
    refresh_report = build_flagship_asset_refresh_report(check_remote=check_remote)
    obsolescence_audit = build_flagship_asset_obsolescence_audit()

    for payload in (contract, refresh_report, obsolescence_audit):
        if isinstance(payload, FlagshipAssetRootContract):
            output_path = repo_root / payload.contract_path
        elif isinstance(payload, FlagshipAssetRefreshReport):
            output_path = repo_root / payload.report_path
        else:
            output_path = repo_root / payload.audit_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            payload.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        written.append(str(output_path.relative_to(repo_root)))

    for entry in contract.entries:
        source_locator_path = repo_root / entry.source_locator_manifest_path
        source_locator_path.write_text(
            json.dumps(
                {
                    "package_id": entry.package_id,
                    "workflow_family": entry.workflow_family,
                    "asset_root": entry.asset_root,
                    "remote_sources": [
                        source.model_dump(mode="json")
                        for source in entry.remote_sources
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        citation_manifest_path = repo_root / entry.citation_manifest_path
        citation_manifest_path.write_text(
            json.dumps(
                {
                    "package_id": entry.package_id,
                    "workflow_family": entry.workflow_family,
                    "citations": [
                        citation.model_dump(mode="json") for citation in entry.citations
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        generated_boundary_path = repo_root / entry.generated_boundary_path
        generated_boundary_path.write_text(
            json.dumps(
                {
                    "package_id": entry.package_id,
                    "workflow_family": entry.workflow_family,
                    "generated_boundaries": [
                        boundary.model_dump(mode="json")
                        for boundary in entry.generated_boundaries
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        rebuild_instructions_path = repo_root / entry.rebuild_instructions_path
        rebuild_instructions_path.write_text(
            "\n".join(
                (
                    f"# Rebuild {entry.workflow_family.upper()} Flagship Asset Root",
                    "",
                    f"Asset root: `{entry.asset_root}`",
                    "",
                    "Rebuild discipline:",
                    "",
                    "- refresh copied snapshots from the tracked upstream repo paths in `source_locator_manifest.json`",
                    "- rerun the flagship asset maintenance command to regenerate package metadata and reports",
                    "- confirm the shared freshness report and obsolescence audit still match the rebuilt package",
                    "",
                    "Command:",
                    "",
                    "```bash",
                    _REFRESH_COMMAND,
                    "```",
                    "",
                    f"Expected wall time: `{entry.expected_wall_time_minutes}` minutes",
                    f"Expected disk footprint: `{entry.expected_disk_footprint_mb}` MB",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        written.extend(
            (
                entry.source_locator_manifest_path,
                entry.citation_manifest_path,
                entry.generated_boundary_path,
                entry.rebuild_instructions_path,
            )
        )
    return tuple(written)


__all__ = [
    "FlagshipAssetBoundaryKind",
    "FlagshipAssetFreshnessEntry",
    "FlagshipAssetObsolescenceAudit",
    "FlagshipAssetObsolescenceEntry",
    "FlagshipAssetRefreshReport",
    "FlagshipAssetRootContract",
    "FlagshipAssetRootEntry",
    "FlagshipCitationReference",
    "FlagshipGeneratedBoundaryRecord",
    "FlagshipRemoteAvailabilityCheck",
    "FlagshipRemoteAvailabilityStatus",
    "FlagshipRemoteSource",
    "build_flagship_asset_obsolescence_audit",
    "build_flagship_asset_refresh_report",
    "build_flagship_asset_root_contract",
    "flagship_asset_contract_path",
    "flagship_asset_obsolescence_audit_path",
    "flagship_asset_refresh_report_path",
    "flagship_asset_root",
    "list_flagship_asset_root_entries",
    "write_flagship_asset_support_files",
]
