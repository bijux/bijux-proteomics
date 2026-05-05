# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pydantic import ValidationError
import pytest

from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics_knowledge.evidence import EvidenceBundle


def test_knowledge_evidence_models_use_foundation_primitives() -> None:
    bundle = EvidenceBundle(bundle_id="bundle-foundation", target_id="target-knowledge")

    assert issubclass(EvidenceBundle, JsonModel)
    assert isinstance(bundle.document_schema, DocumentSchema)

    with pytest.raises(ValidationError):
        EvidenceBundle(bundle_id="bundle-foundation", target_id="Target Knowledge")
