# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned catalog of scientific proof fixtures for hard biological cases."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics_foundation import JsonModel

_SCIENTIFIC_FIXTURE_ROOT = (
    "packages/bijux-proteomics-core/tests/fixtures/scientific_cases"
)


class ScientificFixtureCaseKind(StrEnum):
    """Hard biological cases that must keep proof-ready fixtures."""

    SHARED_PEPTIDES = "shared_peptides"
    ISOFORMS = "isoforms"
    CONTAMINANTS = "contaminants"
    DECOYS = "decoys"
    MISSING_SAMPLES = "missing_samples"
    AMBIGUOUS_PTM_SITES = "ambiguous_ptm_sites"
    BAD_TMT_CHANNELS = "bad_tmt_channels"
    POOR_DIA_RUN = "poor_dia_run"
    CHIMERIC_SPECTRUM = "chimeric_spectrum"


class ScientificFixtureAsset(JsonModel):
    """One file-backed asset that participates in a scientific proof case."""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(..., min_length=1)
    repo_relative_path: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class ScientificFixtureRowExpectation(JsonModel):
    """Expected accepted or rejected row counts for one fixture asset."""

    model_config = ConfigDict(extra="forbid")

    asset_role: str = Field(..., min_length=1)
    row_kind: str = Field(..., min_length=1)
    expected_count: int = Field(..., ge=0)


class ScientificFixtureManifest(JsonModel):
    """Durable manifest for one hard scientific proof fixture."""

    model_config = ConfigDict(extra="forbid")

    fixture_id: str = Field(..., min_length=1)
    case_kind: ScientificFixtureCaseKind
    owner_surface: str = Field(..., min_length=1)
    input_assets: tuple[ScientificFixtureAsset, ...] = Field(default_factory=tuple)
    accepted_rows: tuple[ScientificFixtureRowExpectation, ...] = Field(
        default_factory=tuple
    )
    rejected_rows: tuple[ScientificFixtureRowExpectation, ...] = Field(
        default_factory=tuple
    )
    biological_interpretation: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_expectations(self) -> ScientificFixtureManifest:
        if not self.input_assets:
            raise ValueError("scientific fixture must keep at least one input asset")
        if not self.accepted_rows:
            raise ValueError(
                "scientific fixture must keep accepted-row expectations explicit"
            )
        if not self.rejected_rows:
            raise ValueError(
                "scientific fixture must keep rejected-row expectations explicit"
            )
        asset_roles = tuple(asset.role for asset in self.input_assets)
        if len(set(asset_roles)) != len(asset_roles):
            raise ValueError("scientific fixture asset roles must stay unique")
        valid_roles = set(asset_roles)
        for expectation in (*self.accepted_rows, *self.rejected_rows):
            if expectation.asset_role not in valid_roles:
                raise ValueError(
                    "scientific fixture expectations must reference declared asset roles"
                )
        return self


class ScientificFixtureCatalog(JsonModel):
    """Catalog of scientific proof fixtures that back biological hard cases."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ScientificFixtureManifest, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _validate_entries(self) -> ScientificFixtureCatalog:
        fixture_ids = tuple(entry.fixture_id for entry in self.entries)
        if len(set(fixture_ids)) != len(fixture_ids):
            raise ValueError("scientific fixture ids must stay unique")
        kinds = tuple(entry.case_kind for entry in self.entries)
        if len(set(kinds)) != len(kinds):
            raise ValueError("scientific fixture case kinds must stay unique")
        return self


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def scientific_fixture_repo_path(repo_relative_path: str) -> Path:
    """Resolve one repo-relative scientific fixture path."""

    return _repo_root() / repo_relative_path


def _validate_fixture_paths(manifest: ScientificFixtureManifest) -> None:
    missing_paths = [
        asset.repo_relative_path
        for asset in manifest.input_assets
        if not scientific_fixture_repo_path(asset.repo_relative_path).is_file()
    ]
    if missing_paths:
        joined = ", ".join(sorted(missing_paths))
        raise FileNotFoundError(
            f"scientific fixture assets are missing from the repository: {joined}"
        )


def _scientific_fixture(
    *,
    fixture_id: str,
    case_kind: ScientificFixtureCaseKind,
    owner_surface: str,
    input_assets: tuple[ScientificFixtureAsset, ...],
    accepted_rows: tuple[ScientificFixtureRowExpectation, ...],
    rejected_rows: tuple[ScientificFixtureRowExpectation, ...],
    biological_interpretation: str,
    note: str,
) -> ScientificFixtureManifest:
    manifest = ScientificFixtureManifest(
        fixture_id=fixture_id,
        case_kind=case_kind,
        owner_surface=owner_surface,
        input_assets=input_assets,
        accepted_rows=accepted_rows,
        rejected_rows=rejected_rows,
        biological_interpretation=biological_interpretation,
        note=note,
    )
    _validate_fixture_paths(manifest)
    return manifest


def build_scientific_fixture_catalog() -> ScientificFixtureCatalog:
    """Return the owned scientific proof fixtures for hard biological cases."""

    entries = (
        _scientific_fixture(
            fixture_id="scientific_fixture:shared_peptides",
            case_kind=ScientificFixtureCaseKind.SHARED_PEPTIDES,
            owner_surface="identification.protein_coverage_review",
            input_assets=(
                ScientificFixtureAsset(
                    role="psm_table",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/psm/"
                        "protein_inference_results.tsv"
                    ),
                    note=(
                        "multi-protein peptide assignments force shared-peptide "
                        "coverage accounting instead of one-protein happy-path rollup"
                    ),
                ),
                ScientificFixtureAsset(
                    role="protein_fasta",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/fasta/"
                        "protein_inference.fasta"
                    ),
                    note=(
                        "the paired FASTA keeps the exact protein sequences needed to "
                        "show which proteins share versus uniquely own peptide evidence"
                    ),
                ),
            ),
            accepted_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="psm_table",
                    row_kind="psm_rows",
                    expected_count=5,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="protein_fasta",
                    row_kind="protein_rows",
                    expected_count=4,
                ),
            ),
            rejected_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="psm_table",
                    row_kind="rejected_psm_rows",
                    expected_count=0,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="protein_fasta",
                    row_kind="rejected_protein_rows",
                    expected_count=0,
                ),
            ),
            biological_interpretation=(
                "shared peptide evidence must stay explicit because three proteins "
                "participate in non-unique support while only two proteins retain "
                "unique peptide evidence"
            ),
            note=(
                "this fixture proves that shared peptide pressure survives parsing, "
                "FDR filtering, and protein coverage interpretation"
            ),
        ),
        _scientific_fixture(
            fixture_id="scientific_fixture:isoforms",
            case_kind=ScientificFixtureCaseKind.ISOFORMS,
            owner_surface="sequences.fasta_deduplication",
            input_assets=(
                ScientificFixtureAsset(
                    role="isoform_fasta",
                    repo_relative_path=(
                        f"{_SCIENTIFIC_FIXTURE_ROOT}/isoform_reference.fasta"
                    ),
                    note=(
                        "the fixture carries one canonical accession, one distinct "
                        "isoform accession, and one duplicate isoform header so "
                        "isoform identity and duplicate pressure are both visible"
                    ),
                ),
            ),
            accepted_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="isoform_fasta",
                    row_kind="protein_rows",
                    expected_count=3,
                ),
            ),
            rejected_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="isoform_fasta",
                    row_kind="rejected_protein_rows",
                    expected_count=0,
                ),
            ),
            biological_interpretation=(
                "canonical and isoform accessions must remain distinct biological "
                "entities even when one isoform header is duplicated and later "
                "deduplicated"
            ),
            note=(
                "this fixture keeps isoform fidelity file-backed instead of relying "
                "only on inline test strings"
            ),
        ),
        _scientific_fixture(
            fixture_id="scientific_fixture:contaminants",
            case_kind=ScientificFixtureCaseKind.CONTAMINANTS,
            owner_surface="identification.contaminant_audit",
            input_assets=(
                ScientificFixtureAsset(
                    role="psm_table",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/psm/"
                        "contaminant_results.tsv"
                    ),
                    note=(
                        "the PSM table contains both pure contaminant and mixed "
                        "contaminant-target evidence so contaminant posture cannot be "
                        "reduced to one trivial carryover row"
                    ),
                ),
                ScientificFixtureAsset(
                    role="contaminant_fasta",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/fasta/"
                        "external_contaminants.fasta"
                    ),
                    note=(
                        "the paired contaminant FASTA documents the biological source "
                        "panel behind the contaminant references present in the PSM table"
                    ),
                ),
            ),
            accepted_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="psm_table",
                    row_kind="psm_rows",
                    expected_count=3,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="contaminant_fasta",
                    row_kind="protein_rows",
                    expected_count=2,
                ),
            ),
            rejected_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="psm_table",
                    row_kind="rejected_psm_rows",
                    expected_count=0,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="contaminant_fasta",
                    row_kind="rejected_protein_rows",
                    expected_count=0,
                ),
            ),
            biological_interpretation=(
                "contaminant evidence must separate pure contaminant carryover from "
                "mixed contaminant-target matches because those two cases change how "
                "protein inference and audit posture are interpreted"
            ),
            note=(
                "this fixture proves that contaminant-heavy evidence remains biologically "
                "inspectable instead of collapsing into one boolean flag"
            ),
        ),
        _scientific_fixture(
            fixture_id="scientific_fixture:decoys",
            case_kind=ScientificFixtureCaseKind.DECOYS,
            owner_surface="sequences.target_decoy_validation",
            input_assets=(
                ScientificFixtureAsset(
                    role="target_decoy_fasta",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/fasta/"
                        "target_decoy_valid.fasta"
                    ),
                    note=(
                        "paired target and decoy protein entries keep exact target-decoy "
                        "completeness visible at the FASTA layer"
                    ),
                ),
            ),
            accepted_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="target_decoy_fasta",
                    row_kind="protein_rows",
                    expected_count=4,
                ),
            ),
            rejected_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="target_decoy_fasta",
                    row_kind="rejected_protein_rows",
                    expected_count=0,
                ),
            ),
            biological_interpretation=(
                "target-decoy validation must confirm complete target-decoy pairing so "
                "downstream FDR reasoning does not silently run on a partial database"
            ),
            note=(
                "this fixture proves complete target-decoy coverage with two explicit "
                "target proteins and their two matching decoys"
            ),
        ),
        _scientific_fixture(
            fixture_id="scientific_fixture:missing_samples",
            case_kind=ScientificFixtureCaseKind.MISSING_SAMPLES,
            owner_surface="quantification.missingness_review",
            input_assets=(
                ScientificFixtureAsset(
                    role="feature_table",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/quant/"
                        "missing_mechanism_ms1_features.tsv"
                    ),
                    note=(
                        "the MS1 feature table keeps study-like missingness patterns "
                        "where one peptide disappears by condition while another reflects "
                        "technical dropout"
                    ),
                ),
                ScientificFixtureAsset(
                    role="design_table",
                    repo_relative_path=(
                        f"{_SCIENTIFIC_FIXTURE_ROOT}/missing_samples.design.tsv"
                    ),
                    note=(
                        "the paired design table declares control and treatment samples "
                        "explicitly so missingness interpretation does not rely on file naming"
                    ),
                ),
            ),
            accepted_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="feature_table",
                    row_kind="ms1_feature_rows",
                    expected_count=12,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="design_table",
                    row_kind="design_rows",
                    expected_count=4,
                ),
            ),
            rejected_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="feature_table",
                    row_kind="rejected_feature_rows",
                    expected_count=0,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="design_table",
                    row_kind="rejected_design_rows",
                    expected_count=0,
                ),
            ),
            biological_interpretation=(
                "sample-level absence must separate condition-specific biology from "
                "technical failure because BIOPEP disappears only in treatment while "
                "TECHPEP retains one missing control sample"
            ),
            note=(
                "this fixture moves missingness proof away from hand-built tuples and "
                "into a file-backed study design with multiple biological patterns"
            ),
        ),
        _scientific_fixture(
            fixture_id="scientific_fixture:ambiguous_ptm_sites",
            case_kind=ScientificFixtureCaseKind.AMBIGUOUS_PTM_SITES,
            owner_surface="ptm.ambiguity_review",
            input_assets=(
                ScientificFixtureAsset(
                    role="ptm_localization_table",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/ptm/"
                        "localization_results.tsv"
                    ),
                    note=(
                        "the PTM evidence mixes decisive localized sites, shared-peptide "
                        "ambiguity, and one decoy row so localization confidence remains real"
                    ),
                ),
                ScientificFixtureAsset(
                    role="protein_fasta",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/fasta/"
                        "ptm_sites.fasta"
                    ),
                    note=(
                        "the protein reference FASTA provides site positions needed to "
                        "interpret localized and unresolved PTM groups"
                    ),
                ),
            ),
            accepted_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="ptm_localization_table",
                    row_kind="ptm_evidence_rows",
                    expected_count=8,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="protein_fasta",
                    row_kind="protein_rows",
                    expected_count=3,
                ),
            ),
            rejected_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="ptm_localization_table",
                    row_kind="rejected_ptm_evidence_rows",
                    expected_count=0,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="protein_fasta",
                    row_kind="rejected_protein_rows",
                    expected_count=0,
                ),
            ),
            biological_interpretation=(
                "PTM reporting must preserve decisive localized phosphosites separately "
                "from unresolved site groups because ambiguous evidence still carries "
                "biological meaning without claiming one false residue position"
            ),
            note=(
                "this fixture proves that ambiguity is retained as an explicit review surface"
            ),
        ),
        _scientific_fixture(
            fixture_id="scientific_fixture:bad_tmt_channels",
            case_kind=ScientificFixtureCaseKind.BAD_TMT_CHANNELS,
            owner_surface="isotope_labeling.tmt_validation",
            input_assets=(
                ScientificFixtureAsset(
                    role="reporter_table",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/multiplex/"
                        "maxquant_tmt_evidence.tsv"
                    ),
                    note=(
                        "the reporter-ion table omits one declared channel per plex so "
                        "channel-missing and weak-evidence handling are exercised"
                    ),
                ),
                ScientificFixtureAsset(
                    role="design_table",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/multiplex/"
                        "tmt.design.tsv"
                    ),
                    note=(
                        "the design table declares the full expected multiplex channel map "
                        "for two plex groups"
                    ),
                ),
            ),
            accepted_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="reporter_table",
                    row_kind="reporter_rows",
                    expected_count=4,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="design_table",
                    row_kind="design_rows",
                    expected_count=8,
                ),
            ),
            rejected_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="reporter_table",
                    row_kind="rejected_reporter_rows",
                    expected_count=0,
                ),
                ScientificFixtureRowExpectation(
                    asset_role="design_table",
                    row_kind="rejected_design_rows",
                    expected_count=0,
                ),
            ),
            biological_interpretation=(
                "multiplex validation must preserve missing declared channels as weak "
                "or absent evidence because those gaps change normalization and sample "
                "interpretation across the whole plex"
            ),
            note=(
                "this fixture proves that bad channel structure is caught from real "
                "evidence plus explicit multiplex metadata"
            ),
        ),
        _scientific_fixture(
            fixture_id="scientific_fixture:poor_dia_run",
            case_kind=ScientificFixtureCaseKind.POOR_DIA_RUN,
            owner_surface="dia.run_qc",
            input_assets=(
                ScientificFixtureAsset(
                    role="diann_report",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/"
                        "search_result_bundles/diann/diann_run_qc_report.tsv"
                    ),
                    note=(
                        "the DIA-NN report keeps two strong runs plus one weak run with "
                        "severe precursor loss and a decoy row"
                    ),
                ),
            ),
            accepted_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="diann_report",
                    row_kind="diann_rows",
                    expected_count=10,
                ),
            ),
            rejected_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="diann_report",
                    row_kind="rejected_diann_rows",
                    expected_count=0,
                ),
            ),
            biological_interpretation=(
                "run-level DIA QC must flag raw_C as a poor run because precursor and "
                "protein coverage collapse far below the study median"
            ),
            note=(
                "this fixture proves that weak DIA runs are represented as reviewable "
                "study context instead of disappearing during import"
            ),
        ),
        _scientific_fixture(
            fixture_id="scientific_fixture:chimeric_spectrum",
            case_kind=ScientificFixtureCaseKind.CHIMERIC_SPECTRUM,
            owner_surface="identification.best_psm_selection",
            input_assets=(
                ScientificFixtureAsset(
                    role="psm_table",
                    repo_relative_path=(
                        "packages/bijux-proteomics-core/tests/fixtures/psm/"
                        "duplicate_spectrum_results.tsv"
                    ),
                    note=(
                        "the PSM table carries two competing identifications for one "
                        "spectrum so spectrum-level best-hit selection remains explicit"
                    ),
                ),
            ),
            accepted_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="psm_table",
                    row_kind="psm_rows",
                    expected_count=3,
                ),
            ),
            rejected_rows=(
                ScientificFixtureRowExpectation(
                    asset_role="psm_table",
                    row_kind="rejected_psm_rows",
                    expected_count=0,
                ),
            ),
            biological_interpretation=(
                "competing peptide assignments for one spectrum must remain inspectable "
                "because only the stronger score can be promoted without overclaiming "
                "a chimeric or ambiguous MS2 event"
            ),
            note=(
                "this fixture proves that one spectrum can carry multiple candidate "
                "peptides and still yield a deterministic best-PSM interpretation"
            ),
        ),
    )
    return ScientificFixtureCatalog(
        entries=tuple(sorted(entries, key=lambda entry: entry.fixture_id))
    )


def get_scientific_fixture_manifest(
    case_kind: ScientificFixtureCaseKind,
) -> ScientificFixtureManifest:
    """Return the manifest for one hard scientific case."""

    return next(
        entry
        for entry in build_scientific_fixture_catalog().entries
        if entry.case_kind is case_kind
    )


def render_scientific_fixture_catalog_summary_tsv(
    catalog: ScientificFixtureCatalog,
) -> str:
    """Render the scientific fixture catalog into one stable TSV summary."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "fixture_id",
            "case_kind",
            "owner_surface",
            "asset_count",
            "accepted_expectation_count",
            "rejected_expectation_count",
            "biological_interpretation",
        )
    )
    for entry in sorted(catalog.entries, key=lambda item: item.fixture_id):
        writer.writerow(
            (
                entry.fixture_id,
                entry.case_kind.value,
                entry.owner_surface,
                len(entry.input_assets),
                len(entry.accepted_rows),
                len(entry.rejected_rows),
                entry.biological_interpretation,
            )
        )
    return handle.getvalue()
