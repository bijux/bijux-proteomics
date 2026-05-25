# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPack,
    AnnotationPackSummary,
)
from bijux_proteomics.interpretation.complex_enrichment import (
    ComplexMemberKind,
    ComplexMembershipRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics_knowledge.complexes.members import (
    ComplexMembershipConfidence,
    ComplexMembershipResolutionEntry,
    render_complex_membership_resolution_tsv,
    resolve_complex_members,
)


def test_resolve_complex_members_tracks_observed_missing_and_unresolved_inputs() -> None:
    report = resolve_complex_members(
        ("P04637", "Q9Y243", "UNKNOWN1"),
        _annotation_pack(),
    )

    assert report.entries == (
        ComplexMembershipResolutionEntry(
            complex_id="complex:guardian",
            observed_members=("gene:SIGB", "protein:P04637"),
            missing_members=(),
            member_coverage=1.0,
            complex_confidence=ComplexMembershipConfidence.HIGH_CONFIDENCE,
        ),
        ComplexMembershipResolutionEntry(
            complex_id="complex:megacomplex",
            observed_members=("protein:P04637",),
            missing_members=tuple(f"protein:P{i:05d}" for i in range(2, 21)),
            member_coverage=0.05,
            complex_confidence=ComplexMembershipConfidence.LOW_CONFIDENCE,
        ),
    )
    assert report.unresolved_inputs == ("UNKNOWN1",)
    assert report.summary.unresolved_input_count == 1


def test_resolve_complex_members_downgrades_sparse_large_complexes() -> None:
    report = resolve_complex_members(
        ("P04637",),
        _annotation_pack(),
    )

    confidence_by_complex = {entry.complex_id: entry for entry in report.entries}

    assert (
        confidence_by_complex["complex:guardian"].complex_confidence
        is ComplexMembershipConfidence.LOW_CONFIDENCE
    )
    assert confidence_by_complex["complex:guardian"].member_coverage == 0.5
    assert (
        confidence_by_complex["complex:megacomplex"].complex_confidence
        is ComplexMembershipConfidence.LOW_CONFIDENCE
    )
    assert confidence_by_complex["complex:megacomplex"].member_coverage == 0.05
    assert report.summary.low_confidence_complex_count == 2

    rendered = render_complex_membership_resolution_tsv(report.entries)

    assert rendered.splitlines()[0] == (
        "complex_id\tobserved_members\tmissing_members\tmember_coverage\tcomplex_confidence"
    )
    assert "complex:megacomplex\tprotein:P04637\t" in rendered
    assert "\t0.05\tlow_confidence" in rendered


def _annotation_pack() -> AnnotationPack:
    megacomplex_members = (
        ComplexMembershipRecord(
            complex_id="complex:megacomplex",
            complex_name="megacomplex",
            member_kind=ComplexMemberKind.PROTEIN,
            member_id="P04637",
        ),
        *tuple(
            ComplexMembershipRecord(
                complex_id="complex:megacomplex",
                complex_name="megacomplex",
                member_kind=ComplexMemberKind.PROTEIN,
                member_id=f"P{i:05d}",
            )
            for i in range(2, 21)
        ),
    )
    return AnnotationPack(
        source_path="test-complex-pack.json",
        pack_name="complex-members-test-pack",
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
        ),
        complexes=(
            ComplexMembershipRecord(
                complex_id="complex:guardian",
                complex_name="guardian",
                member_kind=ComplexMemberKind.PROTEIN,
                member_id="P04637",
            ),
            ComplexMembershipRecord(
                complex_id="complex:guardian",
                complex_name="guardian",
                member_kind=ComplexMemberKind.GENE,
                member_id="SIGB",
            ),
            *megacomplex_members,
        ),
        summary=AnnotationPackSummary(
            protein_feature_count=2,
            pathway_count=0,
            complex_count=22,
            compartment_count=0,
            drug_target_count=0,
            disease_term_count=0,
            kinase_substrate_count=0,
            ortholog_count=0,
        ),
    )
