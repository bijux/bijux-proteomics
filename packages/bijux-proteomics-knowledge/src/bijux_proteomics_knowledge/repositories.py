# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Repository contracts for evidence and claims."""

from __future__ import annotations

from typing import Protocol

from bijux_proteomics_knowledge.claims import EvidenceClaim
from bijux_proteomics_knowledge.evidence import EvidenceBundle, EvidenceRecord


class EvidenceBundleRepository(Protocol):
    """Persistence contract for evidence bundles."""

    def save_bundle(self, bundle: EvidenceBundle) -> None:
        """Persist an evidence bundle."""

    def load_bundle(self, bundle_id: str) -> EvidenceBundle:
        """Load an evidence bundle by identifier."""

    def list_target_bundles(self, target_id: str) -> list[EvidenceBundle]:
        """List bundles associated with a target."""


class EvidenceRecordRepository(Protocol):
    """Persistence contract for individual evidence records."""

    def save_record(self, record: EvidenceRecord) -> None:
        """Persist one evidence record."""

    def list_target_records(self, target_id: str) -> list[EvidenceRecord]:
        """List evidence records associated with a target."""


class EvidenceClaimRepository(Protocol):
    """Persistence contract for claim documents."""

    def save_claim(self, claim: EvidenceClaim) -> None:
        """Persist an evidence-backed claim."""

    def list_target_claims(self, target_id: str) -> list[EvidenceClaim]:
        """List claims associated with a target."""
