# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark-backed review outputs for release-facing workflow scrutiny."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics import (
    ExternalReviewerBundle,
    ExternalReviewerBundleInput,
    FastaParseMode,
    LabelBasedChannelPolicyEntry,
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    MissingChannelPolicy,
    MultiplexNormalizationPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
    SearchAdapterKind,
    build_label_based_quant_bundle,
    build_label_free_intensity_table,
    build_dia_capability_matrix,
    build_external_reviewer_bundle,
    build_multiplex_channel_balance_diagnostics_report,
    build_ptm_site_ambiguity_report,
    build_ptm_site_table,
    build_review_ready_evidence_bundle,
    build_search_adapter_conformance_report,
    map_ptm_evidence_to_protein_sites,
    normalize_search_results_with_adapter,
    parse_experimental_design_table,
    parse_fasta_document,
    parse_ms1_feature_table,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.dia import DiaCapabilityMatrixEntry, DiaCapabilityStatus
from bijux_proteomics.ptm.review import build_phospho_specific_review_fixture_report
from bijux_proteomics.quantification.review import build_quant_review_bundle
from bijux_proteomics_foundation import JsonModel, fingerprint_model
from bijux_proteomics_foundation.states import SupportState
from bijux_proteomics_knowledge.references import (
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
    get_benchmark_manifest,
)


class BenchmarkReviewClaim(JsonModel):
    """One benchmark-backed claim with explicit support posture and review notes."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    support_state: SupportState
    summary: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    scientific_limits: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkReviewArtifact(JsonModel):
    """One reviewable artifact that anchors a benchmark-backed workflow claim."""

    model_config = ConfigDict(extra="forbid")

    owner_package: str = Field(..., min_length=1)
    surface_name: str = Field(..., min_length=1)
    artifact_kind: str = Field(..., min_length=1)
    artifact_id: str = Field(..., min_length=1)


class WorkflowBenchmarkReview(JsonModel):
    """Release-facing review output for one benchmark-backed workflow path."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    title: str = Field(..., min_length=1)
    reviewer_summary: str = Field(..., min_length=1)
    owner_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    review_artifacts: tuple[BenchmarkReviewArtifact, ...] = Field(default_factory=tuple)
    claim_summaries: tuple[BenchmarkReviewClaim, ...] = Field(default_factory=tuple)
    scientific_limits: tuple[str, ...] = Field(default_factory=tuple)
    comparison_notes: tuple[str, ...] = Field(default_factory=tuple)
    external_reviewer_bundle: ExternalReviewerBundle
    ready_for_release_review: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _require_manifest(benchmark_id: str) -> BenchmarkManifest:
    manifest = get_benchmark_manifest(benchmark_id)
    if manifest is None:
        raise ValueError(f"unknown benchmark manifest: {benchmark_id}")
    return manifest


def _build_external_bundle(
    *,
    bundle_id: str,
    workflow_family: KnowledgeWorkflowFamily,
    artifact_ids: tuple[str, ...],
    summary_lines: tuple[str, ...],
    scientific_limits: tuple[str, ...],
    hash_entries: tuple[str, ...],
) -> ExternalReviewerBundle:
    return build_external_reviewer_bundle(
        ExternalReviewerBundleInput(
            bundle_id=bundle_id,
            schema_refs=(
                "schema.benchmark_manifest.v1",
                f"schema.{workflow_family.value}.review.v1",
            ),
            evidence_pointer_ids=artifact_ids,
            summary_lines=summary_lines,
            hash_ledger_entries=hash_entries,
            reviewer_instructions=(
                "Review owner surfaces, benchmark evidence pointers, and explicit "
                "scientific limits before treating this workflow as release-ready."
            ),
        )
    )


def build_dda_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    source_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a DDA benchmark review from a checked-in external-engine result."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:dda_search_reproducibility"
    )
    if manifest.workflow_family is not KnowledgeWorkflowFamily.DDA:
        raise ValueError("DDA benchmark review requires a DDA workflow manifest")
    result_path = source_path or (_repo_root() / manifest.dataset_locator)
    normalization = normalize_search_results_with_adapter(
        source_path=result_path,
        adapter_kind=SearchAdapterKind.MSFRAGGER,
    )
    conformance = build_search_adapter_conformance_report(normalization)
    review_bundle = build_review_ready_evidence_bundle(
        normalization.normalized_records,
        score_orientation=normalization.adapter_manifest.score_orientation.value,
    )

    field_loss = tuple(
        sorted(
            {
                *conformance.field_accounting.preserved_native_only_columns,
                *conformance.field_accounting.unsupported_columns,
                *conformance.field_accounting.lost_columns,
            }
        )
    )
    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="adapter_normalization",
            support_state=SupportState.SUPPORTED,
            summary="adapter-normalized DDA evidence stays reviewable after external-engine import",
            evidence_refs=(
                manifest.dataset_id,
                review_bundle.document_schema.content_hash or manifest.benchmark_id,
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="target_decoy_semantics",
            support_state=(
                SupportState.SUPPORTED
                if review_bundle.psm_summary.decoy_psms > 0
                else SupportState.AMBIGUOUS
            ),
            summary="review bundle keeps target-decoy evidence visible instead of flattening confidence posture",
            evidence_refs=(f"decoy_psms={review_bundle.psm_summary.decoy_psms}",),
            scientific_limits=(
                "review support weakens if decoy evidence disappears from the normalized result set",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="field_loss_accounting",
            support_state=(
                SupportState.ADVISORY if field_loss else SupportState.SUPPORTED
            ),
            summary="adapter review keeps any preserved-native or unsupported search columns explicit",
            evidence_refs=field_loss or ("no_extra_field_loss",),
            scientific_limits=(
                "native engine-specific columns remain comparison scope notes, not portable scientific claims",
            ),
        ),
    )
    artifact_id = review_bundle.document_schema.content_hash or fingerprint_model(
        review_bundle
    )
    scientific_limits = (*manifest.comparison_notes,)
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, artifact_id),
        summary_lines=(
            "Core owns DDA parsing and adapter normalization.",
            "Intelligence owns the release-facing benchmark review summary.",
            "This benchmark is limited to the checked-in MSFragger fixture and explicit comparison notes.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            artifact_id,
            fingerprint_model(normalization),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        title=manifest.title,
        reviewer_summary=(
            "DDA benchmark review preserves external-engine normalization, target-decoy posture, "
            "and protein-level reviewability for the checked-in MSFragger fixture without pretending it is a full engine rerun."
        ),
        owner_surfaces=(
            "bijux-proteomics-core: identification.search_adapters",
            "bijux-proteomics-core: identification.review_ready_evidence_bundle",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="normalize_search_results_with_adapter",
                artifact_kind="search_adapter_normalization_report",
                artifact_id=fingerprint_model(normalization),
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_review_ready_evidence_bundle",
                artifact_kind="review_ready_evidence_bundle",
                artifact_id=artifact_id,
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=manifest.comparison_notes,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def build_dia_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    source_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a DIA benchmark review from a checked-in external-engine result."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:dia_library_extraction_consistency"
    )
    if manifest.workflow_family is not KnowledgeWorkflowFamily.DIA:
        raise ValueError("DIA benchmark review requires a DIA workflow manifest")
    result_path = source_path or (_repo_root() / manifest.dataset_locator)
    normalization = normalize_search_results_with_adapter(
        source_path=result_path,
        adapter_kind=SearchAdapterKind.SPECTRONAUT,
    )
    review_bundle = build_review_ready_evidence_bundle(
        normalization.normalized_records,
        score_orientation=normalization.adapter_manifest.score_orientation.value,
    )
    capability_matrix = build_dia_capability_matrix(
        (
            DiaCapabilityMatrixEntry(
                surface="adapter_import",
                status=DiaCapabilityStatus.SUPPORTED,
                note="checked-in Spectronaut-style exports normalize into reviewable peptide evidence",
            ),
            DiaCapabilityMatrixEntry(
                surface="transition_alignment",
                status=(
                    DiaCapabilityStatus.SUPPORTED
                    if len(normalization.normalized_records)
                    == review_bundle.psm_summary.total_psms
                    else DiaCapabilityStatus.PARTIAL
                ),
                note="transition-shaped evidence remains reviewable through normalized precursor identifiers",
            ),
            DiaCapabilityMatrixEntry(
                surface="vendor_library_parity",
                status=DiaCapabilityStatus.PARTIAL,
                note="comparison scope is limited to checked-in external-engine exports rather than in-repo vendor execution",
            ),
        )
    )
    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="adapter_normalization",
            support_state=SupportState.SUPPORTED,
            summary="DIA external-engine exports normalize into stable reviewable evidence records",
            evidence_refs=(
                manifest.dataset_id,
                review_bundle.document_schema.content_hash or manifest.benchmark_id,
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="dia_capability_scope",
            support_state=(
                SupportState.ADVISORY
                if capability_matrix.partial_count > 0
                else SupportState.SUPPORTED
            ),
            summary="DIA review output keeps explicit support, partial support, and scope boundaries visible",
            evidence_refs=(
                f"supported={capability_matrix.supported_count}",
                f"partial={capability_matrix.partial_count}",
            ),
            scientific_limits=(
                "direct vendor-library parity is outside the checked-in benchmark scope",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="protein_group_reviewability",
            support_state=(
                SupportState.SUPPORTED
                if review_bundle.protein_summary.total_proteins > 0
                else SupportState.INCOMPLETE
            ),
            summary="review-ready DIA output preserves protein-group context instead of stopping at raw precursor rows",
            evidence_refs=(
                f"protein_groups={review_bundle.protein_summary.total_proteins}",
            ),
        ),
    )
    artifact_id = review_bundle.document_schema.content_hash or fingerprint_model(
        review_bundle
    )
    scientific_limits = (
        *manifest.comparison_notes,
        "DIA review claims stop at checked-in external-engine exports and explicit capability notes.",
    )
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, artifact_id),
        summary_lines=(
            "Core owns DIA-shaped adapter normalization and review-ready evidence assembly.",
            "Intelligence owns the release-facing benchmark review and scope discipline.",
            "This benchmark preserves explicit DIA capability limits instead of implying full vendor parity.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            artifact_id,
            fingerprint_model(capability_matrix),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        title=manifest.title,
        reviewer_summary=(
            "DIA benchmark review turns a checked-in Spectronaut-style export into a reviewable "
            "bundle with explicit capability limits, rather than presenting adapter coverage as full pipeline parity."
        ),
        owner_surfaces=(
            "bijux-proteomics-core: identification.search_adapters",
            "bijux-proteomics-core: dia.capability_matrix",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="normalize_search_results_with_adapter",
                artifact_kind="search_adapter_normalization_report",
                artifact_id=fingerprint_model(normalization),
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_dia_capability_matrix",
                artifact_kind="dia_capability_matrix",
                artifact_id=fingerprint_model(capability_matrix),
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_review_ready_evidence_bundle",
                artifact_kind="review_ready_evidence_bundle",
                artifact_id=artifact_id,
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=manifest.comparison_notes,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def build_ptm_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    localization_path: Path | None = None,
    feature_path: Path | None = None,
    protein_fasta_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a PTM benchmark review from checked-in localization evidence."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:ptm_site_localization_confidence"
    )
    if manifest.workflow_family is not KnowledgeWorkflowFamily.PTM:
        raise ValueError("PTM benchmark review requires a PTM workflow manifest")
    active_localization_path = localization_path or (
        _repo_root() / manifest.dataset_locator
    )
    active_feature_path = feature_path or (
        _repo_root()
        / "packages"
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "ptm"
        / "ptm_features.tsv"
    )
    active_fasta_path = protein_fasta_path or (
        _repo_root()
        / "packages"
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )

    parsed = parse_ptm_localization_tsv(active_localization_path)
    fasta = parse_fasta_document(
        active_fasta_path.read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    protein_sequences = {
        record.canonical_accession: record.residues for record in fasta.accepted_records
    }
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=protein_sequences,
    )
    site_entries = build_ptm_site_table(mappings)
    ambiguity_entries = build_ptm_site_ambiguity_report(site_entries)
    feature_records = parse_ms1_feature_table(active_feature_path).accepted_records
    phospho_review = build_phospho_specific_review_fixture_report(
        site_entries,
        feature_records=feature_records,
        protein_sequences=protein_sequences,
    )

    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="localization_ingestion",
            support_state=(
                SupportState.SUPPORTED
                if parsed.accepted_records and not parsed.rejected_rows
                else SupportState.INCOMPLETE
            ),
            summary="PTM localization evidence ingests into explicit site mappings instead of disappearing into score-only summaries",
            evidence_refs=(
                manifest.dataset_id,
                f"accepted_records={len(parsed.accepted_records)}",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="site_ambiguity_visibility",
            support_state=(
                SupportState.ADVISORY if ambiguity_entries else SupportState.SUPPORTED
            ),
            summary="PTM review keeps site ambiguity explicit instead of overstating localization certainty",
            evidence_refs=(f"ambiguous_sites={len(ambiguity_entries)}",),
            scientific_limits=(
                "ambiguous site groups remain review-critical caveats even when the benchmark path is otherwise complete",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="phospho_review_packet",
            support_state=(
                SupportState.SUPPORTED
                if phospho_review.motif_window_count
                >= len(phospho_review.phospho_site_keys)
                else SupportState.INCOMPLETE
            ),
            summary="PTM benchmark review reaches a phospho-specific review packet with motif and occupancy caveats intact",
            evidence_refs=(
                f"motif_windows={phospho_review.motif_window_count}",
                f"quantified_samples={len(phospho_review.quantified_sample_ids)}",
            ),
        ),
    )
    review_artifact_id = fingerprint_model(phospho_review)
    scientific_limits = (
        *manifest.comparison_notes,
        "PTM review claims remain constrained by explicit ambiguous-site entries and phospho-focused fixture scope.",
    )
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, review_artifact_id),
        summary_lines=(
            "Core owns PTM localization parsing, site mapping, and phospho review assembly.",
            "Intelligence owns the release-facing benchmark review summary.",
            "This benchmark keeps ambiguous-site caveats visible instead of polishing them away.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            review_artifact_id,
            fingerprint_model(parsed),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        title=manifest.title,
        reviewer_summary=(
            "PTM benchmark review turns checked-in localization evidence into a phospho review packet "
            "while preserving explicit ambiguity and motif-scope limits."
        ),
        owner_surfaces=(
            "bijux-proteomics-core: ptm.localization",
            "bijux-proteomics-core: ptm.review",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="parse_ptm_localization_tsv",
                artifact_kind="ptm_localization_parse_report",
                artifact_id=fingerprint_model(parsed),
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_phospho_specific_review_fixture_report",
                artifact_kind="phospho_review_fixture_report",
                artifact_id=review_artifact_id,
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=manifest.comparison_notes,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def build_lfq_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    feature_path: Path | None = None,
    design_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build an LFQ benchmark review from checked-in feature evidence."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:lfq_quantification_repeatability"
    )
    if manifest.workflow_family is not KnowledgeWorkflowFamily.LFQ:
        raise ValueError("LFQ benchmark review requires an LFQ workflow manifest")
    active_feature_path = feature_path or (_repo_root() / manifest.dataset_locator)
    active_design_path = design_path or (
        _repo_root()
        / "packages"
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "quant"
        / "study_scale.design.tsv"
    )

    feature_report = parse_ms1_feature_table(active_feature_path)
    design_report = parse_experimental_design_table(active_design_path)
    quant_review = build_quant_review_bundle(
        feature_report.accepted_records,
        design_entries=design_report.accepted_entries,
    )

    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="feature_ingestion",
            support_state=(
                SupportState.SUPPORTED
                if feature_report.accepted_records and not feature_report.rejected_rows
                else SupportState.INCOMPLETE
            ),
            summary="LFQ benchmark review ingests checked-in feature rows without silently discarding invalid evidence",
            evidence_refs=(
                manifest.dataset_id,
                f"accepted_records={len(feature_report.accepted_records)}",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="quant_review_bundle",
            support_state=SupportState.SUPPORTED,
            summary="LFQ feature evidence reaches a reviewable quant bundle with provenance, missingness, QC, and rollup comparisons",
            evidence_refs=(
                quant_review.artifact_bundle_hash,
                *quant_review.evidence_pointers,
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="qc_and_missingness_limits",
            support_state=SupportState.ADVISORY,
            summary="LFQ review keeps QC and missingness caveats explicit before stronger abundance claims are made",
            evidence_refs=quant_review.caveats or ("no_lfq_caveats",),
            scientific_limits=(
                "repeatability claims remain bounded by the checked-in LFQ study-scale fixture and any QC caveats in the review bundle",
            ),
        ),
    )
    scientific_limits = (
        *manifest.comparison_notes,
        *quant_review.caveats,
    )
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, quant_review.artifact_bundle_hash),
        summary_lines=(
            "Core owns LFQ feature ingestion, normalization, rollup comparison, and QC assembly.",
            "Intelligence owns the release-facing benchmark review summary.",
            "This benchmark limits LFQ support claims to the checked-in study-scale fixture and explicit QC caveats.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            quant_review.artifact_bundle_hash,
            fingerprint_model(quant_review),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        title=manifest.title,
        reviewer_summary=(
            "LFQ benchmark review turns checked-in feature evidence into a reviewable quant bundle "
            "with missingness, QC, and rollup limits kept explicit."
        ),
        owner_surfaces=(
            "bijux-proteomics-core: quantification.feature_ingestion",
            "bijux-proteomics-core: quantification.review",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="parse_ms1_feature_table",
                artifact_kind="ms1_feature_parse_report",
                artifact_id=fingerprint_model(feature_report),
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_quant_review_bundle",
                artifact_kind="quant_review_bundle",
                artifact_id=quant_review.artifact_bundle_hash,
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=manifest.comparison_notes,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def _default_multiplex_policy() -> LabelBasedQuantPolicy:
    return LabelBasedQuantPolicy(
        missing_channel_policy=MissingChannelPolicy.PRESERVE,
        channel_entries=(
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="126",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="127N",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="128N",
                channel_role=LabelBasedChannelRole.CARRIER,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="129N",
                channel_role=LabelBasedChannelRole.REFERENCE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-b",
                multiplex_channel="126",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-b",
                multiplex_channel="127N",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-b",
                multiplex_channel="128N",
                channel_role=LabelBasedChannelRole.CARRIER,
            ),
        ),
    )


def build_multiplex_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    feature_path: Path | None = None,
    design_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a multiplex benchmark review with explicit reporter-channel caveats."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:multiplex_tmtpro_quantification"
    )
    if manifest.workflow_family is not KnowledgeWorkflowFamily.MULTIPLEX:
        raise ValueError(
            "multiplex benchmark review requires a multiplex workflow manifest"
        )
    active_feature_path = feature_path or (_repo_root() / manifest.dataset_locator)
    active_design_path = design_path or (
        _repo_root()
        / "packages"
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "quant"
        / "multiplex.design.tsv"
    )

    feature_report = parse_ms1_feature_table(active_feature_path)
    design_report = parse_experimental_design_table(active_design_path)
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    policy = _default_multiplex_policy()
    quant_bundle = build_label_based_quant_bundle(
        table,
        design_entries=design_report.accepted_entries,
        policy=policy,
    )
    diagnostics = build_multiplex_channel_balance_diagnostics_report(
        table,
        design_entries=design_report.accepted_entries,
        quant_policy=policy,
        normalization_policy=MultiplexNormalizationPolicy(balance_ratio_threshold=1.2),
    )

    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="feature_ingestion",
            support_state=(
                SupportState.SUPPORTED
                if feature_report.accepted_records and not feature_report.rejected_rows
                else SupportState.INCOMPLETE
            ),
            summary="multiplex benchmark review ingests checked-in reporter evidence into a stable channel-aware table",
            evidence_refs=(
                manifest.dataset_id,
                f"accepted_records={len(feature_report.accepted_records)}",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="channel_manifest",
            support_state=(
                SupportState.ADVISORY
                if quant_bundle.missing_channels
                else SupportState.SUPPORTED
            ),
            summary="multiplex review keeps missing or preserved reporter channels explicit instead of treating the plex as complete by default",
            evidence_refs=(
                f"channels={len(quant_bundle.channels)}",
                f"missing_channels={len(quant_bundle.missing_channels)}",
            ),
            scientific_limits=(
                "missing channels remain explicit review caveats even when preserved in the manifest",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="channel_balance_caveats",
            support_state=SupportState.ADVISORY,
            summary="multiplex review surfaces channel imbalance and label-chemistry caveats before stronger biological claims are published",
            evidence_refs=(
                f"flagged_imbalance_count={diagnostics.flagged_imbalance_count}",
                f"missing_channel_count={diagnostics.missing_channel_count}",
            ),
            scientific_limits=(
                "TMTpro-style support claims stop at explicit channel semantics, balance diagnostics, and checked-in chemistry caveats",
            ),
        ),
    )
    bundle_artifact_id = quant_bundle.document_schema.content_hash or fingerprint_model(
        quant_bundle
    )
    scientific_limits = (
        *manifest.comparison_notes,
        *diagnostics.caveats,
    )
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, bundle_artifact_id),
        summary_lines=(
            "Core owns multiplex feature ingestion, channel manifests, and balance diagnostics.",
            "Intelligence owns the release-facing benchmark review summary.",
            "This benchmark limits multiplex release claims to checked-in TMTpro-style channel semantics and explicit caveats.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            bundle_artifact_id,
            fingerprint_model(diagnostics),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        title=manifest.title,
        reviewer_summary=(
            "Multiplex benchmark review turns checked-in reporter evidence into a reviewable "
            "channel manifest with explicit missing-channel, imbalance, and chemistry caveats."
        ),
        owner_surfaces=(
            "bijux-proteomics-core: quantification.label_based_quant_bundle",
            "bijux-proteomics-core: quantification.multiplex_balance",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_label_based_quant_bundle",
                artifact_kind="label_based_quant_bundle",
                artifact_id=bundle_artifact_id,
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_multiplex_channel_balance_diagnostics_report",
                artifact_kind="multiplex_channel_balance_diagnostics",
                artifact_id=fingerprint_model(diagnostics),
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=manifest.comparison_notes,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


__all__ = [
    "BenchmarkReviewArtifact",
    "BenchmarkReviewClaim",
    "WorkflowBenchmarkReview",
    "build_dda_benchmark_review",
    "build_dia_benchmark_review",
    "build_lfq_benchmark_review",
    "build_multiplex_benchmark_review",
    "build_ptm_benchmark_review",
]
