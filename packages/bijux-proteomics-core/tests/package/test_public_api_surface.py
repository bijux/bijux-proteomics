# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics
from bijux_proteomics.public_api import list_core_root_api_entries

EXPECTED_CORE_ROOT_EXPORTS = (
    "DigestPolicy",
    "parse_fasta_document",
    "parse_experimental_design_table",
    "build_normalized_run_bundle",
    "build_fdr_audit_trail",
)


def test_core_public_api_contains_only_curated_root_exports() -> None:
    assert tuple(bijux_proteomics.__all__) == EXPECTED_CORE_ROOT_EXPORTS
    assert all(hasattr(bijux_proteomics, name) for name in EXPECTED_CORE_ROOT_EXPORTS)


def test_core_public_api_excludes_ambiguity_inducing_convenience_exports() -> None:
    removed = {
        "ProgramSpec",
        "ExperimentalDesignEntry",
        "SearchAdapterKind",
        "SpectrumModel",
        "WorkflowTemplateKind",
    }

    assert removed.isdisjoint(bijux_proteomics.__all__)


def test_core_public_api_module_matches_root_exports() -> None:
    assert tuple(entry.export_name for entry in list_core_root_api_entries()) == tuple(
        bijux_proteomics.__all__
    )
