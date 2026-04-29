# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Search-engine adapter contracts over normalized PSM parsing."""

from __future__ import annotations

import hashlib
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import (
    normalize_psm_records,
    parse_psm_tsv,
    PsmParseReport,
    PsmRecord,
    SearchResultColumnMapping,
    SearchResultProvenanceManifest,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class ScoreOrientation(StrEnum):
    """Whether a native engine score is higher-better or lower-better."""

    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"


class SearchAdapterKind(StrEnum):
    """Built-in search adapter identifiers."""

    COMET = "comet"
    MSFRAGGER = "msfragger"
    SAGE = "sage"
    MAXQUANT_EVIDENCE = "maxquant-evidence"
    DIANN = "diann"
    SPECTRONAUT = "spectronaut"
    GENERIC = "generic"


class SearchAdapterManifest(JsonModel):
    """Stable contract describing one search adapter."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    display_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    score_orientation: ScoreOrientation
    native_columns: tuple[str, ...] = Field(default_factory=tuple)
    mapping: SearchResultColumnMapping | None = None
    default_decoy_policy: TargetDecoyLabelPolicy = Field(default_factory=TargetDecoyLabelPolicy)
    supported_extensions: tuple[str, ...] = Field(default_factory=tuple)
    supports_q_value: bool = False
    supports_explicit_decoy_label: bool = False
    supports_protein_refs: bool = False
    supports_config_hash: bool = False


class SearchAdapterCapability(JsonModel):
    """Compact capability row for one search adapter."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    display_name: str = Field(..., min_length=1)
    score_orientation: ScoreOrientation
    supports_q_value: bool
    supports_explicit_decoy_label: bool
    supports_protein_refs: bool
    supports_config_hash: bool
    native_columns: tuple[str, ...] = Field(default_factory=tuple)


class SearchAdapterNormalizationReport(JsonModel):
    """Normalized records plus the adapter manifest that produced them."""

    model_config = ConfigDict(extra="forbid")

    adapter_manifest: SearchAdapterManifest
    parse_report: PsmParseReport
    normalized_records: tuple[PsmRecord, ...] = Field(default_factory=tuple)


class SearchAdapterProvenanceManifest(JsonModel):
    """Stable provenance for one adapter normalization pass."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    adapter_kind: SearchAdapterKind
    adapter_name: str = Field(..., min_length=1)
    adapter_version: str | None = None
    source_path: str = Field(..., min_length=1)
    source_sha256: str = Field(..., min_length=64, max_length=64)
    config_path: str | None = None
    config_sha256: str | None = None
    native_columns: tuple[str, ...] = Field(default_factory=tuple)
    score_orientation: ScoreOrientation
    parse_provenance: SearchResultProvenanceManifest


_COMET_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.COMET,
    display_name="Comet",
    description="Normalize Comet-like tabular search outputs into stable PSM records.",
    score_orientation=ScoreOrientation.LOWER_BETTER,
    native_columns=("scan", "plain_peptide", "charge", "expect", "protein", "target_decoy"),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan",
        peptide="plain_peptide",
        charge="charge",
        score="expect",
        protein_refs="protein",
        decoy_label="target_decoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("decoy", "true", "1"),
        explicit_target_values=("target", "false", "0"),
    ),
    supported_extensions=(".txt", ".tsv"),
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
)

_MSFRAGGER_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.MSFRAGGER,
    display_name="MSFragger",
    description="Normalize MSFragger-like tabular search outputs into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    native_columns=("Spectrum", "Peptide", "Charge", "Hyperscore", "Protein", "IsDecoy"),
    mapping=SearchResultColumnMapping(
        spectrum_id="Spectrum",
        peptide="Peptide",
        charge="Charge",
        score="Hyperscore",
        protein_refs="Protein",
        decoy_label="IsDecoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("1", "decoy", "true"),
        explicit_target_values=("0", "target", "false"),
    ),
    supported_extensions=(".tsv",),
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
)

_SAGE_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.SAGE,
    display_name="Sage",
    description="Normalize Sage-like tabular search outputs into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    native_columns=("scannr", "peptide", "charge", "discriminant_score", "proteins", "label", "q_value"),
    mapping=SearchResultColumnMapping(
        spectrum_id="scannr",
        peptide="peptide",
        charge="charge",
        score="discriminant_score",
        protein_refs="proteins",
        q_value="q_value",
        decoy_label="label",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("decoy", "-1", "1"),
        explicit_target_values=("target", "1", "0"),
    ),
    supported_extensions=(".tsv",),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
)

_MAXQUANT_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
    display_name="MaxQuant evidence",
    description="Normalize MaxQuant evidence-like tables into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    native_columns=("MS/MS scan number", "Modified sequence", "Charge", "Score", "Proteins", "Reverse", "PEP"),
    mapping=SearchResultColumnMapping(
        spectrum_id="MS/MS scan number",
        peptide="Modified sequence",
        charge="Charge",
        score="Score",
        protein_refs="Proteins",
        q_value="PEP",
        decoy_label="Reverse",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="REV__",
        explicit_decoy_values=("+", "decoy", "true", "1"),
        explicit_target_values=("", "target", "false", "0"),
    ),
    supported_extensions=(".txt", ".tsv"),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
)

_DIANN_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.DIANN,
    display_name="DIA-NN",
    description="Normalize DIA-NN report-style tables into stable PSM-like records.",
    score_orientation=ScoreOrientation.LOWER_BETTER,
    native_columns=("Precursor.Id", "Stripped.Sequence", "Precursor.Charge", "Q.Value", "Protein.Ids", "Decoy"),
    mapping=SearchResultColumnMapping(
        spectrum_id="Precursor.Id",
        peptide="Stripped.Sequence",
        charge="Precursor.Charge",
        score="Q.Value",
        protein_refs="Protein.Ids",
        q_value="Q.Value",
        decoy_label="Decoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("1", "true", "decoy"),
        explicit_target_values=("0", "false", "target"),
    ),
    supported_extensions=(".tsv",),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
)

_SPECTRONAUT_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.SPECTRONAUT,
    display_name="Spectronaut",
    description="Normalize Spectronaut-like tables into stable PSM-like records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    native_columns=("EG.PrecursorId", "PEP.StrippedSequence", "FG.Charge", "EG.Cscore", "PG.ProteinAccessions", "EG.IsDecoy"),
    mapping=SearchResultColumnMapping(
        spectrum_id="EG.PrecursorId",
        peptide="PEP.StrippedSequence",
        charge="FG.Charge",
        score="EG.Cscore",
        protein_refs="PG.ProteinAccessions",
        decoy_label="EG.IsDecoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("true", "1", "decoy"),
        explicit_target_values=("false", "0", "target"),
    ),
    supported_extensions=(".tsv",),
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
)

_GENERIC_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.GENERIC,
    display_name="Generic search table",
    description="Normalize a user-mapped generic search-result table into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    native_columns=tuple(),
    mapping=None,
    default_decoy_policy=TargetDecoyLabelPolicy(),
    supported_extensions=(".tsv", ".txt"),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_config_hash=True,
)


def search_adapter_registry() -> dict[SearchAdapterKind, SearchAdapterManifest]:
    """Return the built-in search adapter registry."""
    manifests = (
        _COMET_MANIFEST,
        _MSFRAGGER_MANIFEST,
        _SAGE_MANIFEST,
        _MAXQUANT_MANIFEST,
        _DIANN_MANIFEST,
        _SPECTRONAUT_MANIFEST,
        _GENERIC_MANIFEST,
    )
    return {manifest.adapter_kind: manifest for manifest in manifests}


def get_search_adapter_manifest(adapter_kind: SearchAdapterKind) -> SearchAdapterManifest:
    """Fetch one built-in adapter manifest."""
    return search_adapter_registry()[adapter_kind]


def build_search_adapter_capability_matrix() -> tuple[SearchAdapterCapability, ...]:
    """Build a stable capability matrix over built-in search adapters."""
    rows = [
        SearchAdapterCapability(
            adapter_kind=manifest.adapter_kind,
            display_name=manifest.display_name,
            score_orientation=manifest.score_orientation,
            supports_q_value=manifest.supports_q_value,
            supports_explicit_decoy_label=manifest.supports_explicit_decoy_label,
            supports_protein_refs=manifest.supports_protein_refs,
            supports_config_hash=manifest.supports_config_hash,
            native_columns=manifest.native_columns,
        )
        for manifest in search_adapter_registry().values()
    ]
    return tuple(sorted(rows, key=lambda row: row.adapter_kind.value))


def _hash_file(path: Path | None) -> str | None:
    if path is None:
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_parse_provenance(
    *,
    source_path: Path,
    parse_report: PsmParseReport,
    adapter_manifest: SearchAdapterManifest,
) -> SearchResultProvenanceManifest:
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_result_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchResultProvenanceManifest(
        document_schema=schema,
        source_path=str(source_path),
        source_sha256=_hash_file(source_path),
        total_rows=parse_report.total_rows,
        accepted_rows=len(parse_report.accepted_records),
        rejected_rows=len(parse_report.rejected_rows),
        column_mapping=parse_report.column_mapping,
        decoy_policy=adapter_manifest.default_decoy_policy,
        fdr_policy=None,
    )
    return manifest.model_copy(
        update={"document_schema": manifest.document_schema.with_content_hash(manifest.to_dict())}
    )


def normalize_search_results_with_adapter(
    *,
    source_path: Path,
    adapter_kind: SearchAdapterKind,
    mapping: SearchResultColumnMapping | None = None,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> SearchAdapterNormalizationReport:
    """Normalize one search table with a built-in or user-supplied adapter mapping."""
    manifest = get_search_adapter_manifest(adapter_kind)
    resolved_mapping = mapping or manifest.mapping
    if resolved_mapping is None:
        raise ValueError("generic adapter normalization requires an explicit column mapping")
    parse_report = parse_psm_tsv(
        source_path,
        mapping=resolved_mapping,
        decoy_policy=decoy_policy or manifest.default_decoy_policy,
    )
    return SearchAdapterNormalizationReport(
        adapter_manifest=manifest,
        parse_report=parse_report,
        normalized_records=normalize_psm_records(parse_report.accepted_records),
    )


def build_search_adapter_provenance_manifest(
    *,
    source_path: Path,
    normalization_report: SearchAdapterNormalizationReport,
    adapter_version: str | None = None,
    config_path: Path | None = None,
) -> SearchAdapterProvenanceManifest:
    """Build provenance for one adapter normalization pass."""
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
        native_columns=normalization_report.adapter_manifest.native_columns,
        score_orientation=normalization_report.adapter_manifest.score_orientation,
        parse_provenance=parse_provenance,
    )
    return manifest.model_copy(
        update={"document_schema": manifest.document_schema.with_content_hash(manifest.to_dict())}
    )
