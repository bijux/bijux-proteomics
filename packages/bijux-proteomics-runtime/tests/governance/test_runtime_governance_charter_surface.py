from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.governance.charter import (
    DEFAULT_RUNTIME_CHARTER,
    DEFAULT_RUNTIME_CHARTER_ENTRIES,
    DEFAULT_RUNTIME_MODULE_AUDIT,
    RuntimeCharterCapability,
)

RUNTIME_SRC_ROOT = Path(
    "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime"
)


def test_runtime_governance_charter_keeps_exact_execution_capabilities() -> None:
    assert set(DEFAULT_RUNTIME_CHARTER.capabilities) == {
        RuntimeCharterCapability.CANONICAL_ENTRYPOINTS,
        RuntimeCharterCapability.PROVIDER_BINDING,
        RuntimeCharterCapability.WORKFLOW_EXECUTION,
        RuntimeCharterCapability.REPLAY_AND_RECOVERY,
        RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
    }


def test_runtime_governance_required_modules_exist() -> None:
    required_modules = {
        module_path
        for entry in DEFAULT_RUNTIME_CHARTER_ENTRIES
        for module_path in entry.required_modules
    }

    assert required_modules
    assert all(
        (RUNTIME_SRC_ROOT / module_path).exists() for module_path in required_modules
    )


def test_runtime_governance_module_audit_covers_source_tree() -> None:
    audited_paths = {entry.module_path for entry in DEFAULT_RUNTIME_MODULE_AUDIT}
    source_paths = {
        path.relative_to(RUNTIME_SRC_ROOT).as_posix()
        for path in RUNTIME_SRC_ROOT.rglob("*.py")
    }

    assert audited_paths == source_paths

