# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.contradictions import (
    ClaimContradictionEntry,
    ClaimContradictionSeverity,
    ClaimContradictionType,
    find_claim_contradictions,
    render_claim_contradictions_tsv,
)
from bijux_proteomics_knowledge.memory.models.claims import (
    ClaimStatus,
    EvidenceClaim,
)


def test_find_claim_contradictions_distinguishes_site_specific_residuals_from_real_conflicts() -> (
    None
):
    report = find_claim_contradictions(
        (
            EvidenceClaim(
                claim_id="claim-protein-steady",
                target_id="protein:p11111",
                statement="protein abundance is unchanged",
                condition="treated_vs_control",
                direction="unchanged",
                magnitude=0.05,
                evidence_ids=["evidence-protein"],
                status=ClaimStatus.SUPPORTED,
                confidence=0.95,
            ),
            EvidenceClaim(
                claim_id="claim-site-corrected",
                target_id="ptm_site:p11111:s5:phospho",
                statement="corrected site effect remains strong",
                condition="treated_vs_control",
                direction="increases",
                magnitude=1.8,
                evidence_ids=["evidence-site-corrected"],
                assumptions=[
                    "protein_correction_status=high_confidence_corrected",
                    "mechanism_class=site_specific",
                    "mechanism_reason_code=residual_site_effect_after_correction",
                ],
                status=ClaimStatus.SUPPORTED,
                confidence=0.92,
            ),
            EvidenceClaim(
                claim_id="claim-site-uncorrected",
                target_id="ptm_site:p11111:s9:phospho",
                statement="raw site change is interpreted without protein correction",
                condition="treated_vs_control",
                direction="increases",
                magnitude=1.7,
                evidence_ids=["evidence-site-uncorrected"],
                assumptions=["protein_correction_status=uncorrected"],
                status=ClaimStatus.SUPPORTED,
                confidence=0.9,
            ),
        )
    )

    assert report.entries == (
        ClaimContradictionEntry(
            claim_a="claim-protein-steady",
            claim_b="claim-site-corrected",
            contradiction_type=ClaimContradictionType.SITE_SPECIFIC,
            severity=ClaimContradictionSeverity.LOW,
            evidence_ids=("evidence-protein", "evidence-site-corrected"),
        ),
        ClaimContradictionEntry(
            claim_a="claim-protein-steady",
            claim_b="claim-site-uncorrected",
            contradiction_type=ClaimContradictionType.PROTEIN_SITE_CONTRADICTION,
            severity=ClaimContradictionSeverity.HIGH,
            evidence_ids=("evidence-protein", "evidence-site-uncorrected"),
        ),
    )
    assert report.summary.site_specific_count == 1
    assert report.summary.protein_site_contradiction_count == 1
    assert report.summary.high_severity_count == 1


def test_find_claim_contradictions_keeps_direct_target_opposition_explicit() -> None:
    report = find_claim_contradictions(
        (
            EvidenceClaim(
                claim_id="claim-up",
                target_id="protein:p22222",
                statement="protein increases in treatment",
                condition="treated_vs_control",
                direction="increase",
                magnitude=1.2,
                evidence_ids=["evidence-up"],
                status=ClaimStatus.SUPPORTED,
            ),
            EvidenceClaim(
                claim_id="claim-down",
                target_id="protein:p22222",
                statement="protein decreases in treatment",
                condition="treated_vs_control",
                direction="decrease",
                magnitude=1.1,
                evidence_ids=["evidence-down"],
                status=ClaimStatus.DISPUTED,
            ),
        )
    )

    assert report.entries == (
        ClaimContradictionEntry(
            claim_a="claim-down",
            claim_b="claim-up",
            contradiction_type=ClaimContradictionType.DIRECT_OPPOSITION,
            severity=ClaimContradictionSeverity.HIGH,
            evidence_ids=("evidence-down", "evidence-up"),
        ),
    )
    assert render_claim_contradictions_tsv(report.entries).splitlines()[0] == (
        "claim_a\tclaim_b\tcontradiction_type\tseverity\tevidence_ids"
    )
