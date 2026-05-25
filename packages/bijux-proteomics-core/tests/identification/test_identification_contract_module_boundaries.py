# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from importlib import import_module
from pathlib import Path


_CONTRACT_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "bijux_proteomics"
    / "identification"
    / "contracts"
)
_MAX_CONTRACT_LINES = 1000
_MODULE_EXPORTS = {
    "psm": (
        "PsmRecord",
        "TargetDecoyLabelPolicy",
        "validate_target_decoy_accession_collisions",
    ),
    "psm_io": (
        "parse_psm_tsv",
        "export_psm_tsv",
        "sort_psm_records",
    ),
    "evidence": (
        "PeptideEvidenceEntry",
        "rollup_peptide_evidence",
        "build_protein_summary_report",
    ),
    "score_fdr": (
        "FdrPolicy",
        "calculate_basic_target_decoy_fdr",
        "build_fdr_audit_trail",
    ),
    "fdr_levels": (
        "LevelSpecificFdrReport",
        "calculate_grouped_fdr",
        "verify_fdr_q_value_monotonicity",
    ),
    "grouping": (
        "ProteinGroupEntry",
        "RazorPeptideAssignment",
        "build_razor_peptide_provenance_report",
    ),
    "protein_inference": (
        "ParsimonyVariant",
        "infer_proteins_by_parsimony",
        "compare_parsimony_variants",
    ),
    "protein_review": (
        "CombinedEvidenceReport",
        "build_protein_coverage_map",
        "calculate_picked_protein_fdr",
    ),
    "confidence": (
        "ConfidenceLabel",
        "build_grouped_confidence_report",
        "assign_level_specific_confidence_labels",
    ),
    "review": (
        "ReviewReadyEvidenceBundle",
        "validate_ptm_identification_confidence",
        "build_search_result_provenance_manifest",
    ),
}
_FACADE_EXPORTS = (
    "PsmRecord",
    "parse_psm_tsv",
    "rollup_peptide_evidence",
    "calculate_basic_target_decoy_fdr",
    "calculate_grouped_fdr",
    "RazorPeptideAssignment",
    "build_grouped_confidence_report",
    "build_review_ready_evidence_bundle",
)


def test_identification_contract_modules_stay_within_line_ceiling() -> None:
    line_counts = {
        path.name: sum(1 for _line in path.open(encoding="utf-8"))
        for path in sorted(_CONTRACT_ROOT.glob("*.py"))
    }

    assert line_counts
    assert all(
        count <= _MAX_CONTRACT_LINES for count in line_counts.values()
    ), line_counts


def test_identification_contract_modules_expose_owned_surfaces() -> None:
    for module_name, exports in _MODULE_EXPORTS.items():
        module = import_module(
            f"bijux_proteomics.identification.contracts.{module_name}"
        )
        for export_name in exports:
            assert hasattr(module, export_name), f"{module_name}.{export_name}"


def test_identification_contract_facade_preserves_representative_exports() -> None:
    facade = import_module("bijux_proteomics.identification.contracts")

    for export_name in _FACADE_EXPORTS:
        assert hasattr(facade, export_name), export_name
