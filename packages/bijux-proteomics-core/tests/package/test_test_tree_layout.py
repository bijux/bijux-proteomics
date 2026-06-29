# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

TEST_ROOT = Path("packages/bijux-proteomics-core/tests")
PACKAGE_TEST_ROOT = TEST_ROOT / "package"


def test_root_level_core_tests_stay_empty_after_package_family_split() -> None:
    root_level_tests = {
        path.name for path in TEST_ROOT.glob("test_*.py") if path.is_file()
    }
    package_tests = {
        path.name for path in PACKAGE_TEST_ROOT.glob("test_*.py") if path.is_file()
    }

    assert root_level_tests == set()
    assert package_tests == {
        "test_chemistry_package_surface.py",
        "test_chemistry_public_api_contract.py",
        "test_compatibility_exports.py",
        "test_complexity_ceiling.py",
        "test_confidence_tier_contract.py",
        "test_core_boundary_guards.py",
        "test_cross_package_invariants.py",
        "test_error_class_surface.py",
        "test_foundation_hashing_surface.py",
        "test_foundation_primitives_surface.py",
        "test_identification_owner_facade_surface.py",
        "test_identification_package_surface.py",
        "test_identification_public_api_contract.py",
        "test_import_contracts.py",
        "test_input_naming_surface.py",
        "test_interpretation_public_api_contract.py",
        "test_interpretation_package_surface.py",
        "test_io_package_surface.py",
        "test_lab_public_api_contract.py",
        "test_lab_package_surface.py",
        "test_line_count_ceiling.py",
        "test_matrix_missingness_contract.py",
        "test_minimal_dependency_import_smoke.py",
        "test_optional_dependency_import_smoke.py",
        "test_output_naming_surface.py",
        "test_output_protocol_surface.py",
        "test_output_table_schema_contract.py",
        "test_owner_wrapper_guards.py",
        "test_package_charter.py",
        "test_parallel_artifact_write_contract.py",
        "test_program_surface.py",
        "test_proteoforms_package_surface.py",
        "test_ptm_package_surface.py",
        "test_public_api_surface.py",
        "test_public_function_docstring_contract.py",
        "test_public_function_type_boundary_contract.py",
        "test_quantification_package_surface.py",
        "test_reason_code_registry_surface.py",
        "test_rejected_evidence_contract.py",
        "test_review_package_surface.py",
        "test_search_adapter_package_surface.py",
        "test_semantic_id_contract.py",
        "test_sequences_package_surface.py",
        "test_source_row_lineage_contract.py",
        "test_study_package_surface.py",
        "test_targeted_package_surface.py",
        "test_test_tree_layout.py",
        "test_workflow_output_schema_contract.py",
        "test_workflow_package_surface.py",
        "test_workflow_public_api_surface.py",
        "test_chemistry_contracts_public_api.py",
    }
