# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.public_scrutiny import (
    build_public_artifact_index,
    build_trust_break_page,
    build_trust_next_page,
)


def test_public_artifact_index_covers_release_candidate_and_all_five_workflows() -> None:
    index = build_public_artifact_index()

    assert index.index_id == "flagship-public-artifact-index"
    assert any(
        entry.locator.endswith("flagship-release-candidate.md")
        for entry in index.entries
    )
    assert any(entry.locator == "outsider_review:dda" for entry in index.entries)
    assert any(
        entry.locator.endswith("targeted_external_review_kit.json")
        for entry in index.entries
    )


def test_trust_break_page_names_repository_and_workflow_fragility() -> None:
    page = build_trust_break_page()

    assert page.page_id == "what-breaks-elite-trust"
    assert page.doc_path.endswith("what-breaks-elite-trust.md")
    assert any(entry.workflow_family is None for entry in page.entries)
    assert any(
        "companion rerun dossier" in entry.break_condition
        for entry in page.entries
        if entry.workflow_family is not None
    )


def test_trust_next_page_uses_claim_grounding_strengthening_paths() -> None:
    page = build_trust_next_page()

    assert page.page_id == "what-earns-elite-trust-next"
    assert page.doc_path.endswith("what-earns-elite-trust-next.md")
    assert any(
        "independent rerun dossier" in entry.why_still_thin
        or "external-review kit" in entry.why_still_thin
        for entry in page.entries
        if entry.workflow_family is not None
    )
    assert any(entry.workflow_family is None for entry in page.entries)
