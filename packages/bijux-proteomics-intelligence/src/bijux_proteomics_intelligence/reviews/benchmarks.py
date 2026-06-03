# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility surface for benchmark-backed workflow reviews."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import build_dia_capability_matrix
from bijux_proteomics.dia.benchmarks import (
    build_dia_workflow_scientific_support_report,
    build_targeted_raw_to_reviewed_bundle_report,
    build_targeted_workflow_benchmark_report,
)
from bijux_proteomics.identification import build_review_ready_evidence_bundle
from bijux_proteomics.identification.search_adapters import (
    build_search_adapter_conformance_report,
    normalize_search_results_with_adapter,
)
from bijux_proteomics.ptm import (
    build_ptm_site_ambiguity_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.benchmarks import (
    build_glycopeptide_support_roadmap_report,
    build_ptm_family_credibility_track_report,
    build_ptm_raw_spectrum_validation_lane_report,
)
from bijux_proteomics.ptm.review import build_phospho_specific_review_fixture_report
from bijux_proteomics.quantification import build_label_based_quant_bundle
from bijux_proteomics.quantification.review import (
    build_multiplex_channel_balance_diagnostics_report,
    build_quant_review_bundle,
)
from bijux_proteomics_foundation import fingerprint_model
from bijux_proteomics_knowledge.references.workflows.benchmarks import BenchmarkManifest
from bijux_proteomics_knowledge.references.workflows.scientific_release import (
    build_scientific_release_packet,
)

from .benchmark_reviews.dda import build_dda_benchmark_review as _build_dda_review
from .benchmark_reviews.dia import build_dia_benchmark_review as _build_dia_review
from .benchmark_reviews.models import (
    BenchmarkComparatorPosition,
    BenchmarkReviewArtifact,
    BenchmarkReviewClaim,
    PtmFamilyReleaseTrack,
    ReviewerGroundingState,
    WorkflowBenchmarkReview,
    WorkflowVendorCaveatEntry,
    WorkflowVendorCaveatLedger,
)
from .benchmark_reviews.ptm import build_ptm_benchmark_review as _build_ptm_review
from .benchmark_reviews.quantification import (
    build_lfq_benchmark_review as _build_lfq_review,
)
from .benchmark_reviews.quantification import (
    build_multiplex_benchmark_review as _build_multiplex_review,
)
from .benchmark_reviews.support import require_manifest, require_registry_entry
from .benchmark_reviews.targeted import (
    build_targeted_benchmark_review as _build_targeted_review,
)


def build_dda_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    source_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a DDA benchmark review from a checked-in external-engine result."""

    manifest = benchmark_manifest or require_manifest(
        "benchmark:dda_search_reproducibility"
    )
    return _build_dda_review(
        benchmark_manifest=manifest,
        registry_entry=require_registry_entry(manifest.benchmark_id),
        scientific_release_packet=build_scientific_release_packet(manifest),
        normalize_search_results_with_adapter=normalize_search_results_with_adapter,
        build_search_adapter_conformance_report=build_search_adapter_conformance_report,
        build_review_ready_evidence_bundle=build_review_ready_evidence_bundle,
        fingerprint_model=fingerprint_model,
        source_path=source_path,
    )


def build_dia_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    source_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a DIA benchmark review from a checked-in external-engine result."""

    manifest = benchmark_manifest or require_manifest(
        "benchmark:dia_library_extraction_consistency"
    )
    return _build_dia_review(
        benchmark_manifest=manifest,
        registry_entry=require_registry_entry(manifest.benchmark_id),
        scientific_release_packet=build_scientific_release_packet(manifest),
        normalize_search_results_with_adapter=normalize_search_results_with_adapter,
        build_review_ready_evidence_bundle=build_review_ready_evidence_bundle,
        build_dia_capability_matrix=build_dia_capability_matrix,
        build_dia_workflow_scientific_support_report=(
            build_dia_workflow_scientific_support_report
        ),
        fingerprint_model=fingerprint_model,
        source_path=source_path,
    )


def build_ptm_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    localization_path: Path | None = None,
    feature_path: Path | None = None,
    protein_fasta_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a PTM benchmark review from checked-in localization evidence."""

    manifest = benchmark_manifest or require_manifest(
        "benchmark:ptm_site_localization_confidence"
    )
    return _build_ptm_review(
        benchmark_manifest=manifest,
        registry_entry=require_registry_entry(manifest.benchmark_id),
        scientific_release_packet=build_scientific_release_packet(manifest),
        parse_ptm_localization_tsv=parse_ptm_localization_tsv,
        map_ptm_evidence_to_protein_sites=map_ptm_evidence_to_protein_sites,
        build_ptm_site_table=build_ptm_site_table,
        build_ptm_site_ambiguity_report=build_ptm_site_ambiguity_report,
        build_phospho_specific_review_fixture_report=(
            build_phospho_specific_review_fixture_report
        ),
        build_ptm_raw_spectrum_validation_lane_report=(
            build_ptm_raw_spectrum_validation_lane_report
        ),
        build_ptm_family_credibility_track_report=(
            build_ptm_family_credibility_track_report
        ),
        build_glycopeptide_support_roadmap_report=(
            build_glycopeptide_support_roadmap_report
        ),
        fingerprint_model=fingerprint_model,
        localization_path=localization_path,
        feature_path=feature_path,
        protein_fasta_path=protein_fasta_path,
    )


def build_lfq_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    feature_path: Path | None = None,
    design_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build an LFQ benchmark review from checked-in feature evidence."""

    manifest = benchmark_manifest or require_manifest(
        "benchmark:lfq_quantification_repeatability"
    )
    return _build_lfq_review(
        benchmark_manifest=manifest,
        registry_entry=require_registry_entry(manifest.benchmark_id),
        scientific_release_packet=build_scientific_release_packet(manifest),
        build_quant_review_bundle=build_quant_review_bundle,
        fingerprint_model=fingerprint_model,
        feature_path=feature_path,
        design_path=design_path,
    )


def build_targeted_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    qc_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a targeted benchmark review with explicit control and vendor limits."""

    manifest = benchmark_manifest or require_manifest(
        "benchmark:targeted_transition_quality_control"
    )
    return _build_targeted_review(
        benchmark_manifest=manifest,
        registry_entry=require_registry_entry(manifest.benchmark_id),
        scientific_release_packet=build_scientific_release_packet(manifest),
        build_targeted_workflow_benchmark_report=(
            build_targeted_workflow_benchmark_report
        ),
        build_targeted_raw_to_reviewed_bundle_report=(
            build_targeted_raw_to_reviewed_bundle_report
        ),
        fingerprint_model=fingerprint_model,
        qc_path=qc_path,
    )


def build_multiplex_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    feature_path: Path | None = None,
    design_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a multiplex benchmark review with explicit reporter-channel caveats."""

    manifest = benchmark_manifest or require_manifest(
        "benchmark:multiplex_tmtpro_quantification"
    )
    return _build_multiplex_review(
        benchmark_manifest=manifest,
        registry_entry=require_registry_entry(manifest.benchmark_id),
        scientific_release_packet=build_scientific_release_packet(manifest),
        build_label_based_quant_bundle=build_label_based_quant_bundle,
        build_multiplex_channel_balance_diagnostics_report=(
            build_multiplex_channel_balance_diagnostics_report
        ),
        fingerprint_model=fingerprint_model,
        feature_path=feature_path,
        design_path=design_path,
    )


__all__ = [
    "BenchmarkComparatorPosition",
    "BenchmarkReviewArtifact",
    "BenchmarkReviewClaim",
    "PtmFamilyReleaseTrack",
    "ReviewerGroundingState",
    "WorkflowBenchmarkReview",
    "WorkflowVendorCaveatEntry",
    "WorkflowVendorCaveatLedger",
    "build_dda_benchmark_review",
    "build_dia_benchmark_review",
    "build_lfq_benchmark_review",
    "build_multiplex_benchmark_review",
    "build_ptm_benchmark_review",
    "build_targeted_benchmark_review",
]
