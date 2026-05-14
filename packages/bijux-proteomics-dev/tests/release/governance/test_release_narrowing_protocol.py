from __future__ import annotations

from types import SimpleNamespace

import pytest

from bijux_proteomics_dev.release.governance.release_narrowing_protocol import (
    build_release_narrowing_protocol,
    run,
)


@pytest.mark.slow
def test_release_narrowing_protocol_is_up_to_date() -> None:
    assert run(check=True) == 0


@pytest.mark.slow
def test_release_narrowing_protocol_tracks_live_language_floors() -> None:
    protocol = build_release_narrowing_protocol()
    decisions = {decision.workflow_family: decision for decision in protocol.decisions}

    assert tuple(rule.rule_id for rule in protocol.rules) == (
        "benchmark-asset-quality",
        "black-box-rerunability",
        "acceptance-bars",
        "consequence-evidence",
    )
    assert decisions["multiplex"].allowed_language == "internal_support_only"
    assert any(
        decision.requested_language != decision.allowed_language
        for decision in protocol.decisions
    )


def test_release_narrowing_protocol_demotes_language_when_benchmark_assets_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._authority_rows",
        lambda: (
            SimpleNamespace(
                workflow_family=SimpleNamespace(value="dda"),
                public_release_language="outsider_auditable_bounded",
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._acceptance_by_family",
        lambda: {
            "dda": SimpleNamespace(
                workflow_family=SimpleNamespace(value="dda"),
                public_release_language=SimpleNamespace(
                    value="outsider_auditable_bounded"
                ),
                earned_release_language=SimpleNamespace(
                    value="outsider_auditable_bounded"
                ),
                acceptance_passed=True,
                evidence_paths=(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance/dda_acceptance_sheet.json",
                ),
            )
        },
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._category_by_id",
        lambda: {
            "benchmark-asset-quality": SimpleNamespace(
                ready=False,
                evidence_paths=(
                    "docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md",
                ),
            ),
            "black-box-rerunability": SimpleNamespace(ready=True, evidence_paths=()),
            "consequence-realism": SimpleNamespace(ready=True, evidence_paths=()),
        },
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._kit_by_family",
        lambda: {
            "dda": SimpleNamespace(
                ready_for_outsider_review=True,
                standalone_verifier_report=SimpleNamespace(verified=True),
                artifact_path="artifacts/intelligence/external-review-kits/dda_external_review_kit.json",
            )
        },
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._dossier_by_family",
        lambda: {
            "dda": SimpleNamespace(
                scrutiny_ready=True,
                artifact_path="artifacts/intelligence/independent-reruns/dda_independent_rerun_dossier.json",
            )
        },
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._freshness_by_family",
        dict,
    )

    protocol = build_release_narrowing_protocol()
    decision = protocol.decisions[0]

    assert decision.workflow_family == "dda"
    assert decision.requested_language == "outsider_auditable_bounded"
    assert decision.allowed_language == "review_grade_bounded"
    assert decision.active_rule_ids == ("benchmark-asset-quality",)


def test_release_narrowing_protocol_uses_weaker_earned_acceptance_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._authority_rows",
        lambda: (
            SimpleNamespace(
                workflow_family=SimpleNamespace(value="multiplex"),
                public_release_language="outsider_auditable_bounded",
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._acceptance_by_family",
        lambda: {
            "multiplex": SimpleNamespace(
                workflow_family=SimpleNamespace(value="multiplex"),
                public_release_language=SimpleNamespace(
                    value="outsider_auditable_bounded"
                ),
                earned_release_language=SimpleNamespace(value="internal_support_only"),
                acceptance_passed=False,
                evidence_paths=(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance/multiplex_acceptance_sheet.json",
                ),
            )
        },
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._category_by_id",
        lambda: {
            "benchmark-asset-quality": SimpleNamespace(ready=True, evidence_paths=()),
            "black-box-rerunability": SimpleNamespace(ready=True, evidence_paths=()),
            "consequence-realism": SimpleNamespace(ready=True, evidence_paths=()),
        },
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._kit_by_family",
        dict,
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._dossier_by_family",
        dict,
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._freshness_by_family",
        dict,
    )

    protocol = build_release_narrowing_protocol()
    decision = protocol.decisions[0]

    assert decision.workflow_family == "multiplex"
    assert decision.requested_language == "outsider_auditable_bounded"
    assert decision.allowed_language == "internal_support_only"
    assert decision.active_rule_ids == ("acceptance-bars",)


def test_release_narrowing_protocol_uses_freshness_floor_when_family_review_expires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._authority_rows",
        lambda: (
            SimpleNamespace(
                workflow_family=SimpleNamespace(value="dda"),
                public_release_language="outsider_auditable_bounded",
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._acceptance_by_family",
        lambda: {
            "dda": SimpleNamespace(
                workflow_family=SimpleNamespace(value="dda"),
                public_release_language=SimpleNamespace(
                    value="outsider_auditable_bounded"
                ),
                earned_release_language=SimpleNamespace(
                    value="outsider_auditable_bounded"
                ),
                acceptance_passed=True,
                evidence_paths=(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance/dda_acceptance_sheet.json",
                ),
            )
        },
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._category_by_id",
        lambda: {
            "benchmark-asset-quality": SimpleNamespace(ready=True, evidence_paths=()),
            "black-box-rerunability": SimpleNamespace(ready=True, evidence_paths=()),
            "consequence-realism": SimpleNamespace(ready=True, evidence_paths=()),
        },
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._kit_by_family",
        dict,
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._dossier_by_family",
        dict,
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.release_narrowing_protocol._freshness_by_family",
        lambda: {
            "dda": SimpleNamespace(
                blockers=("benchmark review window expired",),
                release_language_floor="review_grade_bounded",
                evidence_paths=(
                    "docs/04-bijux-proteomics-core/foundation/benchmark-freshness-review.md",
                ),
            )
        },
    )

    protocol = build_release_narrowing_protocol()
    decision = protocol.decisions[0]

    assert decision.workflow_family == "dda"
    assert decision.allowed_language == "review_grade_bounded"
    assert decision.active_rule_ids == ("benchmark-asset-quality",)
