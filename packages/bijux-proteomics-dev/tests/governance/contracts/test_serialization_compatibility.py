from __future__ import annotations

from bijux_proteomics_dev.governance.contracts.serialization_compatibility import (
    build_package_serialization_compatibility_matrix,
)


def test_package_serialization_compatibility_matrix_covers_persisted_packages() -> None:
    matrix = build_package_serialization_compatibility_matrix()
    case_ids = {row.case_id for row in matrix}

    assert case_ids == {
        "foundation-document-schema-1.0.0",
        "foundation-document-schema-1.1.0",
        "knowledge-evidence-bundle-1.0.0",
        "knowledge-evidence-bundle-1.1.0",
        "lab-experiment-plan-1.0.0",
        "lab-experiment-plan-1.1.0",
    }


def test_cross_version_serialization_matrix_stays_compatible_and_stable() -> None:
    matrix = build_package_serialization_compatibility_matrix()
    by_case_id = {row.case_id: row for row in matrix}

    assert all(row.compatible for row in matrix)
    assert all(row.roundtrip_stable for row in matrix)
    assert (
        by_case_id["foundation-document-schema-1.1.0"].compatibility_status
        == "compatible"
    )
    assert "differs from recommended profile version" in " ".join(
        by_case_id["knowledge-evidence-bundle-1.1.0"].notes
    )
    assert "recommended profile version" in " ".join(
        by_case_id["lab-experiment-plan-1.1.0"].notes
    )
