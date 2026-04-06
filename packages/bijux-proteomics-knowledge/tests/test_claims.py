# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    ClaimPolarity,
    ClaimResolutionState,
    ClaimStatus,
    ClaimType,
    ClaimQuery,
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    build_claim,
    close_claim,
    link_evidence_to_claim,
    build_decision_lineage,
    strengthen_claim,
    build_hypothesis_dossier,
    apply_resolution_assay_outcome,
    ResolutionAssayOutcome,
    identify_knowledge_gaps,
    evaluate_claim_consistency,
    evaluate_mechanistic_completeness,
    build_contradiction_matrix,
    audit_claim_evidence_links,
    evaluate_claim_falsifiability,
    validate_claims,
    weaken_claim,
    query_claims,
)


def test_build_decision_lineage_links_supported_claims_to_evidence() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                source_type=EvidenceSourceType.LITERATURE,
                claim="Target is disease-relevant.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    claim = build_claim(
        claim_id="claim-1",
        target_id="target-1",
        statement="Target relevance is supported.",
        evidence_ids=["lit-1"],
        resolution_assays=["repeat relevance assay"],
        status=ClaimStatus.SUPPORTED,
    )
    contradicting_claim = build_claim(
        claim_id="claim-2",
        target_id="target-1",
        statement="Target relevance is contradicted.",
        evidence_ids=["lit-1"],
        contradicting_evidence_ids=["lit-1"],
        resolution_assays=["orthogonal relevance assay"],
        status=ClaimStatus.DISPUTED,
        polarity=ClaimPolarity.CONTRADICTING,
    )

    lineage = build_decision_lineage(bundle, [claim, contradicting_claim], "progression")

    assert lineage.claim_ids == ["claim-1"]
    assert lineage.disputed_claim_ids == ["claim-2"]
    assert lineage.evidence_ids == ["lit-1"]


def test_close_claim_marks_resolution_state_closed() -> None:
    claim = build_claim(
        claim_id="claim-3",
        target_id="target-1",
        statement="Needs resolution",
        evidence_ids=["lit-1"],
        status=ClaimStatus.INSUFFICIENT,
    )

    closed = close_claim(claim)

    assert closed.resolution_state is ClaimResolutionState.CLOSED


def test_link_evidence_to_claim_attaches_bundle_evidence_ids() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-2",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="ev-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                source_type=EvidenceSourceType.LITERATURE,
                claim="Target is disease-relevant.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    claim = build_claim(
        claim_id="claim-4",
        target_id="target-1",
        statement="Linked claim",
        evidence_ids=[],
        status=ClaimStatus.SUPPORTED,
    )

    linked = link_evidence_to_claim(claim, bundle)

    assert linked.evidence_ids == ["ev-1"]


def test_build_claim_supports_structured_decision_metadata() -> None:
    claim = build_claim(
        claim_id="claim-5",
        target_id="target-1",
        statement="Candidate is likely developable at scale.",
        evidence_ids=["ev-1"],
        status=ClaimStatus.SUPPORTED,
        claim_type=ClaimType.DEVELOPABILITY,
        confidence=0.82,
        contradiction_group="scale-readiness",
        decision_impact="blocking_gate_input",
    )

    assert claim.claim_type is ClaimType.DEVELOPABILITY
    assert claim.confidence == 0.82
    assert claim.contradiction_group == "scale-readiness"


def test_build_claim_supports_mechanistic_structure_fields() -> None:
    claim = build_claim(
        claim_id="claim-6",
        target_id="target-1",
        statement="Treatment increases phospho-signal in cells.",
        evidence_ids=["ev-2"],
        status=ClaimStatus.SUPPORTED,
        subject="target-1",
        relation="increases",
        object="phospho-signal",
        condition="cellular assay under treatment",
        direction="up",
        magnitude=1.6,
    )

    assert claim.subject == "target-1"
    assert claim.relation == "increases"
    assert claim.object == "phospho-signal"
    assert claim.direction == "up"


def test_claim_strength_update_helpers_adjust_confidence() -> None:
    claim = build_claim(
        claim_id="claim-7",
        target_id="target-1",
        statement="initial claim",
        evidence_ids=["ev-1"],
        status=ClaimStatus.SUPPORTED,
        confidence=0.5,
    )
    strengthened, gain = strengthen_claim(claim, delta=0.2, rationale="new orthogonal assay")
    weakened, loss = weaken_claim(strengthened, delta=0.4, rationale="contradictory evidence")

    assert gain.updated_confidence == 0.7
    assert loss.updated_confidence == 0.3
    assert weakened.status is ClaimStatus.DISPUTED


def test_query_claims_filters_by_status_type_and_polarity() -> None:
    claims = [
        build_claim(
            claim_id="claim-a",
            target_id="target-1",
            statement="efficacy support",
            evidence_ids=["ev-1"],
            status=ClaimStatus.SUPPORTED,
            claim_type=ClaimType.EFFICACY,
            polarity=ClaimPolarity.SUPPORTING,
        ),
        build_claim(
            claim_id="claim-b",
            target_id="target-1",
            statement="safety caution",
            evidence_ids=["ev-2"],
            status=ClaimStatus.DISPUTED,
            claim_type=ClaimType.SAFETY,
            polarity=ClaimPolarity.CONTRADICTING,
        ),
    ]

    filtered = query_claims(
        claims,
        ClaimQuery(
            target_id="target-1",
            status=ClaimStatus.SUPPORTED,
            claim_type=ClaimType.EFFICACY,
            polarity=ClaimPolarity.SUPPORTING,
        ),
    )

    assert [claim.claim_id for claim in filtered] == ["claim-a"]


def test_query_claims_supports_confidence_and_resolution_filters() -> None:
    claims = [
        build_claim(
            claim_id="claim-open-high",
            target_id="target-1",
            statement="open claim",
            evidence_ids=["ev-1"],
            status=ClaimStatus.SUPPORTED,
            confidence=0.82,
            decision_impact="blocking_gate_input",
            contradiction_group="group-1",
        ),
        build_claim(
            claim_id="claim-closed-low",
            target_id="target-1",
            statement="closed claim",
            evidence_ids=["ev-2"],
            status=ClaimStatus.SUPPORTED,
            confidence=0.51,
            resolution_state=ClaimResolutionState.CLOSED,
            decision_impact="supporting_context",
            contradiction_group="group-2",
        ),
    ]

    filtered = query_claims(
        claims,
        ClaimQuery(
            target_id="target-1",
            minimum_confidence=0.7,
            resolution_state=ClaimResolutionState.OPEN,
            decision_impact="blocking_gate_input",
            contradiction_group="group-1",
        ),
    )

    assert [claim.claim_id for claim in filtered] == ["claim-open-high"]


def test_validate_claims_requires_mechanistic_structure_and_evidence() -> None:
    issues = validate_claims(
        [
            build_claim(
                claim_id="claim-missing-shape",
                target_id="target-1",
                statement="mechanistic claim with missing structure",
                evidence_ids=[],
                status=ClaimStatus.SUPPORTED,
                claim_type=ClaimType.MECHANISTIC,
            )
        ]
    )

    assert {issue.code for issue in issues} == {
        "claim-evidence-missing",
        "mechanistic-structure-missing",
        "resolution-assays-missing",
    }


def test_validate_claims_requires_contradicting_evidence_ids() -> None:
    issues = validate_claims(
        [
            build_claim(
                claim_id="claim-contradicting",
                target_id="target-1",
                statement="signal contradicts efficacy assumption",
                evidence_ids=["ev-1"],
                status=ClaimStatus.DISPUTED,
                polarity=ClaimPolarity.CONTRADICTING,
                resolution_assays=["repeat assay in orthogonal system"],
            )
        ]
    )

    assert any(issue.code == "contradicting-evidence-missing" for issue in issues)


def test_validate_claims_requires_balanced_contradiction_group() -> None:
    issues = validate_claims(
        [
            build_claim(
                claim_id="claim-a",
                target_id="target-1",
                statement="one-sided support",
                evidence_ids=["ev-1"],
                status=ClaimStatus.SUPPORTED,
                polarity=ClaimPolarity.SUPPORTING,
                contradiction_group="group-1",
            ),
            build_claim(
                claim_id="claim-b",
                target_id="target-1",
                statement="another one-sided support",
                evidence_ids=["ev-2"],
                status=ClaimStatus.SUPPORTED,
                polarity=ClaimPolarity.SUPPORTING,
                contradiction_group="group-1",
            ),
        ]
    )

    assert any(issue.code == "contradiction-group-polarity-unbalanced" for issue in issues)


def test_validate_claims_rejects_closed_claim_with_insufficient_status() -> None:
    issues = validate_claims(
        [
            build_claim(
                claim_id="claim-closed",
                target_id="target-1",
                statement="closed but unresolved",
                evidence_ids=["ev-1"],
                status=ClaimStatus.INSUFFICIENT,
                resolution_state=ClaimResolutionState.CLOSED,
            )
        ]
    )

    assert any(issue.code == "closed-insufficient-claim" for issue in issues)


def test_build_hypothesis_dossier_summarizes_support_contradiction_and_assays() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-hypothesis",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="ev-1",
                kind=EvidenceKind.LITERATURE,
                title="lit",
                source="pmid",
                claim="supports progression",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    support_claim = build_claim(
        claim_id="claim-support",
        target_id="target-1",
        statement="support claim",
        evidence_ids=["ev-1"],
        status=ClaimStatus.SUPPORTED,
        confidence=0.8,
        resolution_assays=["orthogonal cellular assay"],
    )
    contradict_claim = build_claim(
        claim_id="claim-contradict",
        target_id="target-1",
        statement="contradict claim",
        evidence_ids=["ev-1"],
        contradicting_evidence_ids=["ev-1"],
        status=ClaimStatus.DISPUTED,
        polarity=ClaimPolarity.CONTRADICTING,
        resolution_assays=["target engagement assay"],
    )

    dossier = build_hypothesis_dossier(
        bundle,
        [support_claim, contradict_claim],
        decision_tag="progression",
    )

    assert dossier.supporting_claim_ids == ["claim-support"]
    assert dossier.contradicting_claim_ids == ["claim-contradict"]
    assert sorted(dossier.required_resolution_assays) == [
        "orthogonal cellular assay",
        "target engagement assay",
    ]


def test_apply_resolution_assay_outcome_updates_claim_confidence() -> None:
    claim = build_claim(
        claim_id="claim-assay-outcome",
        target_id="target-1",
        statement="candidate improves target engagement",
        evidence_ids=["ev-1"],
        status=ClaimStatus.SUPPORTED,
        confidence=0.6,
        resolution_assays=["target engagement assay"],
    )
    updated, update = apply_resolution_assay_outcome(
        claim,
        ResolutionAssayOutcome(
            claim_id="claim-assay-outcome",
            assay_name="target engagement assay",
            confirms_claim=False,
            confidence_delta=0.25,
        ),
    )

    assert updated.confidence == 0.35
    assert updated.status is ClaimStatus.DISPUTED
    assert "does not confirm claim direction" in update.rationale


def test_identify_knowledge_gaps_reports_open_claim_and_decisive_gap() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-gap",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="ev-gap-1",
                kind=EvidenceKind.LITERATURE,
                title="support",
                source="pmid",
                claim="supports progression",
                decision_tags=["progression"],
                confidence=0.75,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    claim = build_claim(
        claim_id="claim-gap-1",
        target_id="target-1",
        statement="claim still open",
        evidence_ids=["ev-gap-1"],
        status=ClaimStatus.SUPPORTED,
        resolution_assays=["orthogonal assay"],
    )

    gaps = identify_knowledge_gaps(bundle, [claim], decision_tag="progression")

    assert any(gap.gap_code == "open-claims-require-resolution" for gap in gaps)
    assert any(gap.gap_code == "no-decisive-evidence" for gap in gaps)


def test_evaluate_claim_consistency_reports_unbalanced_contradiction_groups() -> None:
    claims = [
        build_claim(
            claim_id="claim-consistency-a",
            target_id="target-1",
            statement="support claim",
            evidence_ids=["ev-1"],
            status=ClaimStatus.SUPPORTED,
            contradiction_group="group-1",
            polarity=ClaimPolarity.SUPPORTING,
            resolution_assays=["assay-a"],
        ),
        build_claim(
            claim_id="claim-consistency-b",
            target_id="target-1",
            statement="another support claim",
            evidence_ids=["ev-2"],
            status=ClaimStatus.SUPPORTED,
            contradiction_group="group-1",
            polarity=ClaimPolarity.SUPPORTING,
            resolution_assays=["assay-b"],
        ),
    ]
    report = evaluate_claim_consistency(claims, target_id="target-1")

    assert report.claim_count == 2
    assert report.inconsistent_groups == ["group-1"]


def test_evaluate_mechanistic_completeness_reports_missing_structure() -> None:
    claim = build_claim(
        claim_id="claim-mech-1",
        target_id="target-1",
        statement="partial mechanistic claim",
        evidence_ids=["ev-1"],
        status=ClaimStatus.SUPPORTED,
        claim_type=ClaimType.MECHANISTIC,
        subject="target-1",
        resolution_assays=["assay"],
    )
    report = evaluate_mechanistic_completeness(claim)

    assert report.completeness_score < 1.0
    assert "relation" in report.missing_fields


def test_build_contradiction_matrix_marks_group_opposition() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-matrix",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="ev-m1",
                kind=EvidenceKind.LITERATURE,
                title="lit",
                source="pmid",
                claim="support",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    claim_a = build_claim(
        claim_id="claim-matrix-a",
        target_id="target-1",
        statement="support",
        evidence_ids=["ev-m1"],
        status=ClaimStatus.SUPPORTED,
        polarity=ClaimPolarity.SUPPORTING,
        contradiction_group="cg-1",
        resolution_assays=["assay"],
    )
    claim_b = build_claim(
        claim_id="claim-matrix-b",
        target_id="target-1",
        statement="oppose",
        evidence_ids=["ev-m1"],
        contradicting_evidence_ids=["ev-m1"],
        status=ClaimStatus.DISPUTED,
        polarity=ClaimPolarity.CONTRADICTING,
        contradiction_group="cg-1",
        resolution_assays=["assay"],
    )
    matrix = build_contradiction_matrix(bundle, [claim_a, claim_b], decision_tag="progression")

    assert matrix.relations["claim-matrix-a|claim-matrix-b"] == "same-group-opposing-polarity"


def test_audit_claim_evidence_links_reports_missing_bundle_references() -> None:
    bundle = EvidenceBundle(bundle_id="bundle-link", target_id="target-1")
    claim = build_claim(
        claim_id="claim-link-1",
        target_id="target-1",
        statement="missing links",
        evidence_ids=["ev-missing-support"],
        contradicting_evidence_ids=["ev-missing-contradiction"],
        status=ClaimStatus.DISPUTED,
        polarity=ClaimPolarity.CONTRADICTING,
        resolution_assays=["assay"],
    )
    issues = audit_claim_evidence_links(bundle, [claim])

    assert {issue.code for issue in issues} == {
        "support-evidence-missing-in-bundle",
        "contradiction-evidence-missing-in-bundle",
    }


def test_evaluate_claim_falsifiability_flags_missing_fields() -> None:
    claim = build_claim(
        claim_id="claim-f",
        target_id="target-1",
        statement="needs structure",
        evidence_ids=["ev-1"],
        status=ClaimStatus.INSUFFICIENT,
    )

    report = evaluate_claim_falsifiability(claim)

    assert report.falsifiable is False
    assert "resolution_assays" in report.missing_fields
