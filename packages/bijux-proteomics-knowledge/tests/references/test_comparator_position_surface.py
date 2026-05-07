# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.comparator_positions import (
    ComparatorPositionKind,
    build_comparator_position_report,
)


def test_comparator_position_report_contains_real_known_losses_and_wins() -> None:
    report = build_comparator_position_report()

    kinds = {entry.kind for entry in report.entries}

    assert ComparatorPositionKind.KNOWN_LOSS in kinds
    assert ComparatorPositionKind.KNOWN_WIN in kinds


def test_comparator_position_report_names_multiple_specific_losses() -> None:
    report = build_comparator_position_report()
    losses = [entry for entry in report.entries if entry.kind is ComparatorPositionKind.KNOWN_LOSS]

    assert len(losses) >= 3
    assert any("calibration" in entry.title for entry in losses)
    assert any("missingness" in entry.title or "evidence-loss" in entry.title for entry in losses)


def test_comparator_position_report_names_stricter_review_wins() -> None:
    report = build_comparator_position_report()
    wins = [entry for entry in report.entries if entry.kind is ComparatorPositionKind.KNOWN_WIN]

    assert any("protein-level evidence" in entry.title for entry in wins)
    assert any("ambiguity divergence" in entry.title for entry in wins)
