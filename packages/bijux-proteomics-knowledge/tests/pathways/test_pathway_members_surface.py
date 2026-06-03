# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPack,
    AnnotationPackSummary,
    load_annotation_pack,
    render_annotation_pack_json,
)
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMemberKind,
    PathwayMembershipRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics_knowledge.pathways.members import (
    PathwayCoverageConfidenceStatus,
    PathwayMembershipResolutionEntry,
    render_pathway_membership_resolution_tsv,
    resolve_pathway_members,
)


def test_resolve_pathway_members_tracks_matched_missing_and_unresolved_inputs() -> None:
    report = resolve_pathway_members(
        ("P04637", "Q9Y243", "UNKNOWN1"),
        _annotation_pack(),
    )

    assert report.entries == (
        PathwayMembershipResolutionEntry(
            pathway_id="pathway:guardian_response",
            matched_members=("gene:SIGB", "protein:P04637"),
            missing_members=(),
            coverage_fraction=1.0,
            unresolved_inputs=("UNKNOWN1",),
        ),
        PathwayMembershipResolutionEntry(
            pathway_id="pathway:stress_network",
            matched_members=("gene:SIGB", "protein:P04637"),
            missing_members=("gene:MAPK1", "protein:O14920"),
            coverage_fraction=0.5,
            unresolved_inputs=("UNKNOWN1",),
        ),
    )
    confidence_by_pathway = {
        entry.pathway_id: entry.confidence_status for entry in report.confidence_entries
    }
    assert (
        confidence_by_pathway["pathway:guardian_response"]
        is PathwayCoverageConfidenceStatus.HIGH_CONFIDENCE
    )
    assert (
        confidence_by_pathway["pathway:stress_network"]
        is PathwayCoverageConfidenceStatus.HIGH_CONFIDENCE
    )
    assert report.summary.unresolved_input_count == 1


def test_resolve_pathway_members_uses_coverage_to_downgrade_pathway_confidence() -> (
    None
):
    report = resolve_pathway_members(
        ("P04637",),
        _annotation_pack(),
    )

    confidence_by_pathway = {
        entry.pathway_id: entry for entry in report.confidence_entries
    }

    assert confidence_by_pathway["pathway:guardian_response"].coverage_fraction == 0.5
    assert (
        confidence_by_pathway["pathway:guardian_response"].confidence_status
        is PathwayCoverageConfidenceStatus.HIGH_CONFIDENCE
    )
    assert confidence_by_pathway["pathway:stress_network"].coverage_fraction == 0.25
    assert (
        confidence_by_pathway["pathway:stress_network"].confidence_status
        is PathwayCoverageConfidenceStatus.LOW_CONFIDENCE
    )
    assert report.summary.high_confidence_pathway_count == 1
    assert report.summary.low_confidence_pathway_count == 1

    rendered = render_pathway_membership_resolution_tsv(report.entries)

    assert rendered.splitlines() == [
        "pathway_id\tmatched_members\tmissing_members\tcoverage_fraction\tunresolved_inputs",
        "pathway:guardian_response\tprotein:P04637\tgene:SIGB\t0.5\t",
        "pathway:stress_network\tprotein:P04637\tgene:MAPK1;gene:SIGB;protein:O14920\t0.25\t",
    ]


def test_resolve_pathway_members_round_trips_exported_annotation_pack(
    tmp_path: Path,
) -> None:
    original_pack = _annotation_pack()
    exported_path = tmp_path / "pathway_annotation_pack.json"
    exported_path.write_text(
        render_annotation_pack_json(original_pack),
        encoding="utf-8",
    )
    reloaded_pack = load_annotation_pack(exported_path)

    original_report = resolve_pathway_members(
        ("P04637", "Q9Y243", "UNKNOWN1"),
        original_pack,
    )
    reloaded_report = resolve_pathway_members(
        ("P04637", "Q9Y243", "UNKNOWN1"),
        reloaded_pack,
    )

    assert reloaded_report == original_report


def _annotation_pack() -> AnnotationPack:
    return AnnotationPack(
        source_path="test-annotation-pack.json",
        pack_name="pathway-members-test-pack",
        protein_features=(
            ProteinAnnotationRecord(
                protein_ref="P04637",
                gene_symbol="TP53",
                description="tumor protein p53",
            ),
            ProteinAnnotationRecord(
                protein_ref="Q9Y243",
                gene_symbol="SIGB",
                description="stress adaptor beta",
            ),
            ProteinAnnotationRecord(
                protein_ref="O14920",
                gene_symbol="MAPK1",
                description="mitogen activated kinase 1",
            ),
        ),
        pathways=(
            PathwayMembershipRecord(
                pathway_id="pathway:guardian_response",
                pathway_name="guardian response",
                member_kind=PathwayMemberKind.PROTEIN,
                member_id="P04637",
            ),
            PathwayMembershipRecord(
                pathway_id="pathway:guardian_response",
                pathway_name="guardian response",
                member_kind=PathwayMemberKind.GENE,
                member_id="SIGB",
            ),
            PathwayMembershipRecord(
                pathway_id="pathway:stress_network",
                pathway_name="stress network",
                member_kind=PathwayMemberKind.PROTEIN,
                member_id="P04637",
            ),
            PathwayMembershipRecord(
                pathway_id="pathway:stress_network",
                pathway_name="stress network",
                member_kind=PathwayMemberKind.GENE,
                member_id="SIGB",
            ),
            PathwayMembershipRecord(
                pathway_id="pathway:stress_network",
                pathway_name="stress network",
                member_kind=PathwayMemberKind.GENE,
                member_id="MAPK1",
            ),
            PathwayMembershipRecord(
                pathway_id="pathway:stress_network",
                pathway_name="stress network",
                member_kind=PathwayMemberKind.PROTEIN,
                member_id="O14920",
            ),
        ),
        summary=AnnotationPackSummary(
            protein_feature_count=3,
            pathway_count=6,
            complex_count=0,
            compartment_count=0,
            drug_target_count=0,
            disease_term_count=0,
            kinase_substrate_count=0,
            ortholog_count=0,
        ),
    )
