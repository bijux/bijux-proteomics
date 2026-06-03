# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.refusal import (
    ClaimRefusalEntry,
    ClaimRefusalReason,
    ClaimRefusalThresholds,
    refuse_unsupported_claims,
    render_claim_refusal_tsv,
)
from bijux_proteomics_knowledge.memory.models.claims import ClaimStatus, EvidenceClaim


def test_refuse_unsupported_claims_blocks_strong_claims_for_design_qc_peptide_and_localization_failures() -> (
    None
):
    report = refuse_unsupported_claims(
        (
            EvidenceClaim(
                claim_id="claim-invalid-design",
                target_id="protein:p11111",
                statement="protein effect under invalid design",
                evidence_ids=["evidence-1"],
                assumptions=[
                    "design_valid=false",
                    "qc_status=passed",
                    "peptide_support_count=3",
                ],
                status=ClaimStatus.SUPPORTED,
                confidence=0.95,
            ),
            EvidenceClaim(
                claim_id="claim-failed-qc",
                target_id="protein:p22222",
                statement="protein effect under failed qc",
                evidence_ids=["evidence-2"],
                assumptions=[
                    "design_valid=true",
                    "qc_status=failed",
                    "peptide_support_count=3",
                ],
                status=ClaimStatus.SUPPORTED,
                confidence=0.94,
            ),
            EvidenceClaim(
                claim_id="claim-weak-peptides",
                target_id="protein:p33333",
                statement="protein effect with thin peptide support",
                evidence_ids=["evidence-3"],
                assumptions=[
                    "design_valid=true",
                    "qc_status=passed",
                    "peptide_support_count=1",
                ],
                status=ClaimStatus.SUPPORTED,
                confidence=0.93,
            ),
            EvidenceClaim(
                claim_id="claim-low-localization",
                target_id="ptm_site:p44444:s9:phospho",
                statement="ptm effect with weak localization",
                evidence_ids=["evidence-4"],
                assumptions=[
                    "design_valid=true",
                    "qc_status=passed",
                    "peptide_support_count=3",
                    "localization_tier=low",
                ],
                status=ClaimStatus.SUPPORTED,
                confidence=0.96,
            ),
            EvidenceClaim(
                claim_id="claim-allowed",
                target_id="ptm_site:p55555:s11:phospho",
                statement="well-supported ptm effect",
                evidence_ids=["evidence-5"],
                assumptions=[
                    "design_valid=true",
                    "qc_status=passed",
                    "peptide_support_count=4",
                    "localization_tier=high_confidence",
                ],
                status=ClaimStatus.SUPPORTED,
                confidence=0.97,
            ),
        ),
        ClaimRefusalThresholds(
            minimum_strong_claim_confidence=0.8,
            minimum_peptide_support_count=2,
            accepted_localization_tiers=("high_confidence", "localized"),
        ),
    )

    assert report.entries == (
        ClaimRefusalEntry(
            claim_id="claim-invalid-design",
            refused=True,
            refusal_reason=ClaimRefusalReason.INVALID_DESIGN,
            minimum_missing_evidence=("valid_design",),
        ),
        ClaimRefusalEntry(
            claim_id="claim-failed-qc",
            refused=True,
            refusal_reason=ClaimRefusalReason.FAILED_QC,
            minimum_missing_evidence=("passing_qc",),
        ),
        ClaimRefusalEntry(
            claim_id="claim-weak-peptides",
            refused=True,
            refusal_reason=ClaimRefusalReason.WEAK_PEPTIDE_SUPPORT,
            minimum_missing_evidence=("peptide_support_count>=2",),
        ),
        ClaimRefusalEntry(
            claim_id="claim-low-localization",
            refused=True,
            refusal_reason=ClaimRefusalReason.LOW_LOCALIZATION,
            minimum_missing_evidence=("high_confidence", "localized"),
        ),
        ClaimRefusalEntry(
            claim_id="claim-allowed",
            refused=False,
            refusal_reason=None,
            minimum_missing_evidence=(),
        ),
    )
    assert report.summary.refused_claim_count == 4
    assert report.summary.invalid_design_count == 1
    assert report.summary.failed_qc_count == 1
    assert report.summary.weak_peptide_support_count == 1
    assert report.summary.low_localization_count == 1


def test_render_claim_refusal_tsv_preserves_required_columns() -> None:
    report = refuse_unsupported_claims(
        (
            EvidenceClaim(
                claim_id="claim-invalid-design",
                target_id="protein:p11111",
                statement="protein effect under invalid design",
                evidence_ids=["evidence-1"],
                assumptions=[
                    "design_valid=false",
                    "qc_status=passed",
                    "peptide_support_count=3",
                ],
                status=ClaimStatus.SUPPORTED,
                confidence=0.95,
            ),
        )
    )

    assert render_claim_refusal_tsv(report.entries).splitlines()[0] == (
        "claim_id\trefused\trefusal_reason\tminimum_missing_evidence"
    )
