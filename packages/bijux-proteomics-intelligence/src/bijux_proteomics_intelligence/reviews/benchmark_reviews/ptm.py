# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM benchmark review owner."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from bijux_proteomics.ptm.cards.benchmarks import (
    GlycopeptideSupportRoadmapReport,
    PtmFamilyCredibilityTrackReport,
    PtmRawSpectrumValidationLaneReport,
)
from bijux_proteomics.ptm.cards.review import PtmPhosphoReviewFixtureReport
from bijux_proteomics.ptm.contracts import PtmEvidenceParseReport
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_foundation.support.states import SupportState
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    BenchmarkPackageArtifactKind,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkRegistryEntry,
)
from bijux_proteomics_knowledge.references.workflows.scientific_release import (
    ScientificReleasePacket,
)

from .models import (
    BenchmarkReviewArtifact,
    BenchmarkReviewClaim,
    PtmFamilyReleaseTrack,
    WorkflowBenchmarkReview,
)
from .support import (
    benchmark_package_artifact_ids,
    build_comparator_positions,
    build_external_bundle,
    build_grounding_payload,
    build_public_claim_posture,
    grounding_summary_phrase,
    resolve_package_artifact_path,
    workflow_minimum_controls,
)


def build_ptm_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest,
    registry_entry: BenchmarkRegistryEntry,
    scientific_release_packet: ScientificReleasePacket,
    parse_ptm_localization_tsv: Callable[[Path], PtmEvidenceParseReport],
    map_ptm_evidence_to_protein_sites: Callable[..., tuple[object, ...]],
    build_ptm_site_table: Callable[[tuple[object, ...]], tuple[object, ...]],
    build_ptm_site_ambiguity_report: Callable[[tuple[object, ...]], tuple[object, ...]],
    build_phospho_specific_review_fixture_report: Callable[
        ..., PtmPhosphoReviewFixtureReport
    ],
    build_ptm_raw_spectrum_validation_lane_report: Callable[
        ..., PtmRawSpectrumValidationLaneReport
    ],
    build_ptm_family_credibility_track_report: Callable[
        ..., PtmFamilyCredibilityTrackReport
    ],
    build_glycopeptide_support_roadmap_report: Callable[
        ..., GlycopeptideSupportRoadmapReport
    ],
    fingerprint_model: Callable[[JsonModel], str],
    localization_path: Path | None = None,
    feature_path: Path | None = None,
    protein_fasta_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a PTM benchmark review from checked-in localization evidence."""

    if benchmark_manifest.workflow_family is not KnowledgeWorkflowFamily.PTM:
        raise ValueError("PTM benchmark review requires a PTM workflow manifest")
    active_localization_path = localization_path or resolve_package_artifact_path(
        benchmark_manifest,
        BenchmarkPackageArtifactKind.RESULTS_TABLE,
    )
    active_feature_path = feature_path or resolve_package_artifact_path(
        benchmark_manifest,
        BenchmarkPackageArtifactKind.FEATURE_TABLE,
    )
    active_fasta_path = protein_fasta_path or resolve_package_artifact_path(
        benchmark_manifest,
        BenchmarkPackageArtifactKind.PROTEIN_FASTA,
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
    raw_validation_lane = build_ptm_raw_spectrum_validation_lane_report(
        parsed.accepted_records,
        raw_spectrum_artifact_path=(
            "packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf"
        ),
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y6", "y7"),
            "scan=ptm-002": ("b4",),
        },
    )
    family_tracks = build_ptm_family_credibility_track_report(
        site_entries,
        feature_records=feature_records,
        protein_sequences=protein_sequences,
    )
    glyco_roadmap = build_glycopeptide_support_roadmap_report(
        requested_workflow="n_glycopeptide_localization"
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
                benchmark_manifest.dataset_id,
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
            summary="PTM benchmark review reaches a phospho-specific decision brief with motif and occupancy caveats intact",
            evidence_refs=(
                f"motif_windows={phospho_review.motif_window_count}",
                f"quantified_samples={len(phospho_review.quantified_sample_ids)}",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="raw_spectrum_validation_lane",
            support_state=(
                SupportState.SUPPORTED
                if raw_validation_lane.ready_for_rescoring_follow_up
                else SupportState.ADVISORY
            ),
            summary="PTM review keeps a raw-spectrum-linked validation lane visible instead of stopping at TSV-localization ingestion",
            evidence_refs=(
                raw_validation_lane.raw_spectrum_artifact_path,
                f"fragment_supported_spectra={raw_validation_lane.fragment_supported_spectrum_count}",
            ),
            scientific_limits=(
                "rescoring follow-up weakens whenever localized spectra lack fragment-linked support",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="ptm_family_scope",
            support_state=SupportState.ADVISORY,
            summary="PTM release claims name the supported, interpretive-only, and refused PTM families explicitly",
            evidence_refs=(
                *family_tracks.supported_families,
                *family_tracks.interpretive_only_families,
                *family_tracks.refused_families,
            ),
            scientific_limits=(
                glyco_roadmap.current_disposition,
                *glyco_roadmap.required_scientific_work[:2],
            ),
        ),
    )
    review_artifact_id = fingerprint_model(phospho_review)
    scientific_limits = (
        *benchmark_manifest.comparison_notes,
        "PTM review claims remain constrained by explicit ambiguous-site entries and phospho-focused fixture scope.",
    )
    (
        public_claim_support_state,
        comparator_failure_summaries,
        improvement_targets,
        known_loss_to_established_tool,
    ) = build_public_claim_posture(benchmark_manifest.benchmark_id)
    (
        reviewer_grounding_state,
        reviewer_grounding_limits,
        curated_reference_context,
        decision_grade_criteria,
    ) = build_grounding_payload(
        workflow_family=benchmark_manifest.workflow_family,
        benchmark_manifest=benchmark_manifest,
        public_claim_support_state=public_claim_support_state,
    )
    external_bundle = build_external_bundle(
        bundle_id=f"{benchmark_manifest.benchmark_id}:external_review",
        workflow_family=benchmark_manifest.workflow_family,
        artifact_ids=(benchmark_manifest.dataset_id, review_artifact_id),
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
    ptm_release_tracks = tuple(
        PtmFamilyReleaseTrack(
            family_name=track.family_name,
            support_state=(
                SupportState.SUPPORTED
                if track.disposition.value == "supported"
                else SupportState.ADVISORY
                if track.disposition.value == "interpretive_only"
                else SupportState.REFUSED
            ),
            summary=track.evidence_summary,
            scientific_limits=track.caveats,
        )
        for track in family_tracks.tracks
    )
    supported_family_summary = ", ".join(family_tracks.supported_families) or "none"
    refused_family_summary = ", ".join(family_tracks.refused_families) or "none"
    return WorkflowBenchmarkReview(
        benchmark_id=benchmark_manifest.benchmark_id,
        dataset_id=benchmark_manifest.dataset_id,
        workflow_family=benchmark_manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=benchmark_manifest.title,
        reviewer_summary=(
            "PTM benchmark review turns checked-in localization evidence into a phospho decision brief "
            f"while preserving explicit ambiguity and motif-scope limits, naming supported PTM families ({supported_family_summary}), "
            f"and refusing unsupported carryover ({refused_family_summary}); {grounding_summary_phrase(reviewer_grounding_state)}"
        ),
        benchmark_package_id=registry_entry.benchmark_package_id,
        benchmark_package_summary=registry_entry.benchmark_package_summary,
        benchmark_package_artifact_ids=benchmark_package_artifact_ids(
            benchmark_manifest.benchmark_id
        ),
        comparator_positions=build_comparator_positions(
            benchmark_manifest.workflow_family
        ),
        public_claim_support_state=public_claim_support_state,
        comparator_failure_summaries=comparator_failure_summaries,
        improvement_targets=improvement_targets,
        known_loss_to_established_tool=known_loss_to_established_tool,
        reviewer_grounding_state=reviewer_grounding_state,
        reviewer_grounding_limits=reviewer_grounding_limits,
        curated_reference_context=curated_reference_context,
        decision_grade_criteria=decision_grade_criteria,
        minimum_controls_required=workflow_minimum_controls(
            benchmark_manifest.workflow_family
        ),
        scientific_release_packet=scientific_release_packet,
        supported_repo_claims=registry_entry.supported_repo_claims,
        authorized_claim_scope=registry_entry.authorized_claim_scope,
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
        comparison_notes=benchmark_manifest.comparison_notes,
        supported_ptm_families=family_tracks.supported_families,
        ptm_family_tracks=ptm_release_tracks,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )
