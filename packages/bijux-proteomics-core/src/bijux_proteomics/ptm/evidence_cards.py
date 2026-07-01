# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility facade for the canonical PTM evidence-card owner."""

from __future__ import annotations

from bijux_proteomics.ptm.cards.evidence_cards import (
    PtmEvidenceCard,
    PtmEvidenceCardClaim,
    PtmEvidenceCardClaimKind,
    PtmEvidenceCardDifferentialResult,
    PtmEvidenceCardLocalization,
    PtmEvidenceCardLocalizationObservation,
    PtmEvidenceCardMechanismClassification,
    PtmEvidenceCardMotifEvidence,
    PtmEvidenceCardPolicy,
    PtmEvidenceCardProteinCorrection,
    PtmEvidenceCardReport,
    PtmEvidenceCardSummary,
    build_ptm_evidence_card_report,
    render_ptm_evidence_card_summary_tsv,
    render_ptm_evidence_card_tsv,
    render_ptm_evidence_claim_tsv,
)

__all__ = [
    "PtmEvidenceCard",
    "PtmEvidenceCardClaim",
    "PtmEvidenceCardClaimKind",
    "PtmEvidenceCardDifferentialResult",
    "PtmEvidenceCardLocalization",
    "PtmEvidenceCardLocalizationObservation",
    "PtmEvidenceCardMechanismClassification",
    "PtmEvidenceCardMotifEvidence",
    "PtmEvidenceCardPolicy",
    "PtmEvidenceCardProteinCorrection",
    "PtmEvidenceCardReport",
    "PtmEvidenceCardSummary",
    "build_ptm_evidence_card_report",
    "render_ptm_evidence_card_summary_tsv",
    "render_ptm_evidence_card_tsv",
    "render_ptm_evidence_claim_tsv",
]
