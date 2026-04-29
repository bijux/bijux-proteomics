from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.integration_patterns import (
    accepted_integration_patterns,
    validate_integration_patterns,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_workspace_integration_patterns_match_current_package_boundaries() -> None:
    validations = validate_integration_patterns(REPO_ROOT)
    by_pattern_id = {validation.pattern.pattern_id: validation for validation in validations}

    assert all(validation.valid for validation in validations)
    assert (
        by_pattern_id["runtime-to-core"].pattern.handoff_mode == "direct_dependency"
    )
    assert (
        by_pattern_id["core-to-knowledge"].pattern.handoff_mode == "artifact_handoff"
    )
    assert (
        by_pattern_id["intelligence-to-lab"].pattern.handoff_mode == "artifact_handoff"
    )


def test_integration_pattern_catalog_stays_narrow_and_explicit() -> None:
    patterns = {pattern.pattern_id: pattern for pattern in accepted_integration_patterns()}

    assert patterns.keys() == {
        "runtime-to-core",
        "core-to-knowledge",
        "intelligence-to-lab",
    }
    assert patterns["runtime-to-core"].required_edges == (
        ("bijux-proteomics-runtime", "bijux-proteomics-core"),
    )
