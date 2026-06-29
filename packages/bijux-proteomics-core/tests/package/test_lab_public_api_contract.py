# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab.public_api import (
    LAB_ROOT_FACADE_BUDGET,
    LAB_ROOT_FACADE_OWNERS,
    QC_FACADE_BUDGET,
    QC_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
)


def test_lab_facade_ledgers_fit_surface_budgets() -> None:
    cases = (
        ("lab", LAB_ROOT_FACADE_BUDGET.max_public_symbols, LAB_ROOT_FACADE_OWNERS),
        ("lab.qc", QC_FACADE_BUDGET.max_public_symbols, QC_FACADE_OWNERS),
    )

    for facade_name, max_public_symbols, owners in cases:
        export_names, _ = build_lazy_export_index(facade_owner_modules(owners))
        assert len(export_names) <= max_public_symbols, (
            f"{facade_name} facade exports {len(export_names)} symbols, "
            f"exceeding its budget of {max_public_symbols}"
        )


def test_lab_facade_ledgers_keep_export_names_unambiguous() -> None:
    root_exports, root_owner_map = build_lazy_export_index(
        facade_owner_modules(LAB_ROOT_FACADE_OWNERS)
    )
    qc_exports, qc_owner_map = build_lazy_export_index(facade_owner_modules(QC_FACADE_OWNERS))

    assert len(root_exports) == len(set(root_exports))
    assert len(qc_exports) == len(set(qc_exports))
    assert set(root_exports) == set(root_owner_map)
    assert set(qc_exports) == set(qc_owner_map)


def test_lab_facade_ledgers_preserve_representative_exports() -> None:
    root_exports, _ = build_lazy_export_index(facade_owner_modules(LAB_ROOT_FACADE_OWNERS))
    qc_exports, _ = build_lazy_export_index(facade_owner_modules(QC_FACADE_OWNERS))

    assert "build_lcms_run_qc_report" in root_exports
    assert "transition_assay_progression" in root_exports
    assert "build_qc_evidence_manifest" in qc_exports
    assert "QcThresholdPolicy" in qc_exports
