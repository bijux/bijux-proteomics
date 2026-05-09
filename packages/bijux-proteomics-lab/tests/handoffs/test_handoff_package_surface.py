# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_lab.handoffs as handoffs


def test_handoff_package_surface_keeps_curated_public_entrypoints() -> None:
    expected = {
        "AlternativeAssayPlanOption",
        "HandoffAuthorityOwner",
        "HandoffExplanation",
        "HandoffSupportLevel",
        "HandoffSupportStatement",
        "TargetedTransitionReview",
        "TargetedTransitionReviewEntry",
        "TransitionReviewDisposition",
        "build_handoff_explanation",
        "build_lims_export_bundle",
        "compare_alternative_assay_plans",
        "refuse_irresponsible_assay_handoff",
    }

    assert expected <= set(handoffs.__all__)


def test_handoff_package_surface_drops_infrastructure_leakage() -> None:
    leaked_names = {"ConfigDict", "Field", "JsonModel", "StrEnum", "TYPE_CHECKING"}

    assert leaked_names.isdisjoint(set(dir(handoffs)))
