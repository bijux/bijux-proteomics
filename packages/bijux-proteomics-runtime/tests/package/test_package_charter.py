# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.governance.charter import (
    DEFAULT_RUNTIME_CHARTER,
    DEFAULT_RUNTIME_CHARTER_ENTRIES,
    DEFAULT_RUNTIME_MODULE_AUDIT,
    RuntimeCharterCapability,
    RuntimeModuleClassification,
    list_runtime_capabilities,
    list_runtime_charter_entries,
)

RUNTIME_SRC_ROOT = Path(
    "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime"
)


def test_runtime_charter_exposes_exact_execution_capabilities() -> None:
    assert list_runtime_capabilities() == DEFAULT_RUNTIME_CHARTER.capabilities
    assert set(DEFAULT_RUNTIME_CHARTER.capabilities) == {
        RuntimeCharterCapability.CANONICAL_ENTRYPOINTS,
        RuntimeCharterCapability.PROVIDER_BINDING,
        RuntimeCharterCapability.WORKFLOW_EXECUTION,
        RuntimeCharterCapability.REPLAY_AND_RECOVERY,
        RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
    }


def test_runtime_charter_keeps_non_owned_surfaces_explicit() -> None:
    assert list_runtime_charter_entries() == DEFAULT_RUNTIME_CHARTER_ENTRIES
    assert DEFAULT_RUNTIME_CHARTER.excluded_ownership == (
        "scientific normalization and domain schema ownership",
        "reference curation and ontology maintenance",
        "analytical prioritization and recommendation judgment",
        "laboratory queueing, protocol control, and observed-outcome authority",
    )


def test_runtime_module_audit_covers_every_source_module() -> None:
    audited_paths = {entry.module_path for entry in DEFAULT_RUNTIME_MODULE_AUDIT}
    source_paths = {
        path.relative_to(RUNTIME_SRC_ROOT).as_posix()
        for path in RUNTIME_SRC_ROOT.rglob("*.py")
    }

    assert audited_paths == source_paths


def test_runtime_module_audit_rejects_generic_wrong_owner_and_dead_entries() -> None:
    invalid_entries = {
        entry.module_path: entry.classification
        for entry in DEFAULT_RUNTIME_MODULE_AUDIT
        if entry.classification
        in {
            RuntimeModuleClassification.GENERIC_INFRASTRUCTURE,
            RuntimeModuleClassification.WRONG_PACKAGE_LOGIC,
            RuntimeModuleClassification.DEAD_WEIGHT,
        }
    }

    assert invalid_entries == {}


def test_runtime_thin_abstractions_are_only_namespace_initializers() -> None:
    thin_paths = {
        entry.module_path
        for entry in DEFAULT_RUNTIME_MODULE_AUDIT
        if entry.classification is RuntimeModuleClassification.THIN_ABSTRACTION
    }

    assert thin_paths
    assert all(path.endswith("__init__.py") for path in thin_paths)


def test_runtime_owner_modules_avoid_too_thin_non_initializer_files() -> None:
    undersized = []
    for path in sorted(RUNTIME_SRC_ROOT.rglob("*.py")):
        relative = path.relative_to(RUNTIME_SRC_ROOT).as_posix()
        if relative.endswith("__init__.py"):
            continue
        if len(path.read_text(encoding="utf-8").splitlines()) < 10:
            undersized.append(relative)

    assert undersized == []
