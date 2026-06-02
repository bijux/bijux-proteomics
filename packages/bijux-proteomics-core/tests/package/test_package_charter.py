# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

from bijux_proteomics.governance.charter import (
    DEFAULT_CORE_CHARTER,
    DEFAULT_CORE_DOMAIN_ENTRIES,
    DEFAULT_CORE_MODULE_AUDIT,
    CoreModuleClassification,
    CoreScientificDomainFamily,
    list_core_domain_entries,
    list_core_domain_families,
)

CORE_SRC_ROOT = Path("packages/bijux-proteomics-core/src/bijux_proteomics")
REMOVED_COMPATIBILITY_PATHS = {
    "advanced_format_ingestion.py",
    "execution_backend.py",
    "execution_contracts.py",
    "execution/providers.py",
    "formats.py",
    "assays.py",
    "context.py",
    "criteria.py",
    "constraints.py",
    "digestion.py",
    "enzyme_rule_provenance.py",
    "isotope_adduct_annotation.py",
    "interfaces/api.py",
    "lifecycle.py",
    "modified_peptide_conflicts.py",
    "open_search_unknown_mod.py",
    "operating_model.py",
    "peptide_uniqueness_audit.py",
    "program_spec.py",
    "protease_digest_comparison.py",
    "repositories.py",
    "reviews.py",
    "runner.py",
    "runtime_adapter.py",
    "schema.py",
    "serialization.py",
    "stable_isotope_labeling.py",
    "spectra.py",
    "targets.py",
    "theoretical_fragment_reference.py",
    "validation.py",
    "workflow/reproducibility.py",
    "workflow/runs.py",
    "workflow/runtime.py",
    "workflow_runtime.py",
}


def test_core_charter_exposes_exact_scientific_domain_families() -> None:
    assert list_core_domain_families() == DEFAULT_CORE_CHARTER.domain_families
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


def test_core_charter_keeps_non_owned_surfaces_explicit() -> None:
    assert list_core_domain_entries() == DEFAULT_CORE_DOMAIN_ENTRIES
    assert DEFAULT_CORE_CHARTER.excluded_ownership == (
        "runtime provider binding and run orchestration",
        "knowledge reference curation and ontology registries",
        "intelligence ranking and recommendation judgment",
        "lab scheduling, protocol control, and operational readiness authority",
    )


def test_core_module_audit_covers_every_source_module() -> None:
    audited_paths = {entry.module_path for entry in DEFAULT_CORE_MODULE_AUDIT}
    source_paths = {
        path.relative_to(CORE_SRC_ROOT).as_posix()
        for path in CORE_SRC_ROOT.rglob("*.py")
    }

    assert audited_paths == source_paths


def test_core_module_audit_rejects_wrong_owner_entries() -> None:
    invalid_entries = {
        entry.module_path: entry.classification
        for entry in DEFAULT_CORE_MODULE_AUDIT
        if entry.classification is CoreModuleClassification.WRONG_PACKAGE_LOGIC
    }

    assert invalid_entries == {}


def test_core_thin_abstractions_stay_limited_to_package_initializers() -> None:
    thin_paths = {
        entry.module_path
        for entry in DEFAULT_CORE_MODULE_AUDIT
        if entry.classification is CoreModuleClassification.THIN_ABSTRACTION
    }

    assert thin_paths
    for path in thin_paths:
        if path.endswith("__init__.py"):
            continue
        source = (CORE_SRC_ROOT / path).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=path)
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(
                getattr(node, "value", None), ast.Constant
            ):
                if isinstance(node.value.value, str):
                    continue
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                continue
            assert isinstance(node, ast.ImportFrom), path
            assert node.module is not None and node.module.startswith(
                "bijux_proteomics."
            ), path
            assert all(alias.name == "*" for alias in node.names), path


def test_core_compatibility_exports_do_not_restore_removed_root_modules() -> None:
    compatibility_paths = {
        entry.module_path
        for entry in DEFAULT_CORE_MODULE_AUDIT
        if entry.classification is CoreModuleClassification.COMPATIBILITY_EXPORT
    }

    assert compatibility_paths.isdisjoint(REMOVED_COMPATIBILITY_PATHS)
