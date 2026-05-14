# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_lab.governance.charter import (
    DEFAULT_LAB_CHARTER,
    DEFAULT_LAB_MODULE_AUDIT,
    LabCharterCapability,
    LabModuleClassification,
)

LAB_SRC_ROOT = Path("packages/bijux-proteomics-lab/src/bijux_proteomics_lab")


def test_lab_charter_defines_exact_operational_capabilities() -> None:
    capabilities = {entry.capability for entry in DEFAULT_LAB_CHARTER}

    assert capabilities == {
        LabCharterCapability.ASSAY_PLANNING,
        LabCharterCapability.QUEUEING,
        LabCharterCapability.PROGRESSION,
        LabCharterCapability.HANDOFF_PACKETS,
        LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
    }


def test_lab_module_audit_covers_every_source_module() -> None:
    audited_paths = {entry.module_path for entry in DEFAULT_LAB_MODULE_AUDIT}
    source_paths = {
        path.relative_to(LAB_SRC_ROOT).as_posix() for path in LAB_SRC_ROOT.rglob("*.py")
    }

    assert audited_paths == source_paths


def test_lab_module_audit_rejects_duplicate_and_wrong_owner_entries() -> None:
    duplicate_or_wrong = {
        entry.module_path: entry.classification
        for entry in DEFAULT_LAB_MODULE_AUDIT
        if entry.classification
        in {
            LabModuleClassification.DUPLICATE_SCHEMA,
            LabModuleClassification.WRONG_PACKAGE_LOGIC,
        }
    }

    assert duplicate_or_wrong == {}


def test_only_curated_compatibility_paths_remain_thin_abstraction() -> None:
    thin_paths = {
        entry.module_path
        for entry in DEFAULT_LAB_MODULE_AUDIT
        if entry.classification is LabModuleClassification.THIN_ABSTRACTION
    }

    assert thin_paths == {
        "__init__.py",
        "benchmarks/__init__.py",
        "design/__init__.py",
        "governance/__init__.py",
        "handoffs/__init__.py",
        "lifecycle/__init__.py",
        "outcomes/__init__.py",
        "planning/__init__.py",
        "readiness/__init__.py",
        "reconciliation/__init__.py",
    }
