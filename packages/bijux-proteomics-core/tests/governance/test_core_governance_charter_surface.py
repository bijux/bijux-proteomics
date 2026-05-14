from __future__ import annotations

from pathlib import Path

from bijux_proteomics.governance.charter import (
    DEFAULT_CORE_CHARTER,
    DEFAULT_CORE_DOMAIN_ENTRIES,
    DEFAULT_CORE_MODULE_AUDIT,
    CoreScientificDomainFamily,
)

CORE_SRC_ROOT = Path("packages/bijux-proteomics-core/src/bijux_proteomics")


def test_core_governance_charter_keeps_exact_domain_families() -> None:
    assert set(DEFAULT_CORE_CHARTER.domain_families) == {
        CoreScientificDomainFamily.PROGRAM_GOVERNANCE,
        CoreScientificDomainFamily.SEQUENCE_AND_CHEMISTRY,
        CoreScientificDomainFamily.INGESTION_AND_IDENTIFICATION,
        CoreScientificDomainFamily.QUANTIFICATION_AND_STUDY,
        CoreScientificDomainFamily.PTM_AND_DIA,
        CoreScientificDomainFamily.REVIEW_AND_HANDOFF,
        CoreScientificDomainFamily.WORKFLOW_CONTRACTS,
        CoreScientificDomainFamily.PACKAGE_SURFACE,
    }


def test_core_governance_required_modules_exist() -> None:
    required_modules = {
        module_path
        for entry in DEFAULT_CORE_DOMAIN_ENTRIES
        for module_path in entry.required_modules
    }

    assert required_modules
    assert all(
        (CORE_SRC_ROOT / module_path).exists() for module_path in required_modules
    )


def test_core_governance_module_audit_covers_source_tree() -> None:
    audited_paths = {entry.module_path for entry in DEFAULT_CORE_MODULE_AUDIT}
    source_paths = {
        path.relative_to(CORE_SRC_ROOT).as_posix()
        for path in CORE_SRC_ROOT.rglob("*.py")
    }

    assert audited_paths == source_paths
