# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.adoption import (
    UsageSimplificationCandidate,
    build_product_simplification_by_real_usage_report,
)


def test_build_product_simplification_by_real_usage_report_counts_decisions() -> None:
    report = build_product_simplification_by_real_usage_report(
        (
            UsageSimplificationCandidate(
                surface_id="workflow.legacy-mode",
                recent_usage_count=0,
                user_value_summary="no external users in the last three months",
                decision="remove",
            ),
            UsageSimplificationCandidate(
                surface_id="workflow.experimental-debug",
                recent_usage_count=2,
                user_value_summary="rare specialist use",
                decision="demote",
            ),
            UsageSimplificationCandidate(
                surface_id="workflow.review-core",
                recent_usage_count=42,
                user_value_summary="core adoption path",
                decision="keep",
            ),
        )
    )

    assert report.remove_count == 1
    assert report.demote_count == 1
    assert report.keep_count == 1
