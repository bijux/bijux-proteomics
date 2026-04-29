# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics
import bijux_proteomics_intelligence
import bijux_proteomics_knowledge
import bijux_proteomics_lab


def test_core_public_api_contains_expected_exports() -> None:
    assert "ProgramSpec" in bijux_proteomics.__all__
    assert "ExecutionBackend" in bijux_proteomics.__all__
    assert "ProteinSequence" in bijux_proteomics.__all__
    assert "FastaParseReport" in bijux_proteomics.__all__
    assert "generate_decoy_records" in bijux_proteomics.__all__
    assert "validate_target_decoy_database" in bijux_proteomics.__all__
    assert "digest_sequence" in bijux_proteomics.__all__
    assert "protease_registry" in bijux_proteomics.__all__
    assert "build_peptide_protein_index" in bijux_proteomics.__all__
    assert "calculate_monoisotopic_peptide_mass" in bijux_proteomics.__all__
    assert "calculate_fragment_ions" in bijux_proteomics.__all__
    assert "modification_registry" in bijux_proteomics.__all__
    assert "canonicalize_modified_peptide" in bijux_proteomics.__all__
    assert "build_peptide_charge_state" in bijux_proteomics.__all__
    assert "approximate_peptide_isotope_envelope" in bijux_proteomics.__all__
    assert "PsmRecord" in bijux_proteomics.__all__
    assert "parse_psm_tsv" in bijux_proteomics.__all__
    assert "rollup_protein_evidence" in bijux_proteomics.__all__
    assert "filter_psms_by_fdr" in bijux_proteomics.__all__
    assert "build_search_result_provenance_manifest" in bijux_proteomics.__all__
    assert "export_psm_tsv" in bijux_proteomics.__all__
    assert "SpectrumModel" in bijux_proteomics.__all__
    assert "parse_mgf" in bijux_proteomics.__all__
    assert "annotate_spectrum_fragments" in bijux_proteomics.__all__
    assert "calculate_spectral_similarity" in bijux_proteomics.__all__
    assert "build_spectrum_provenance_manifest" in bijux_proteomics.__all__


def test_intelligence_public_api_contains_expected_exports() -> None:
    assert "RankingPolicy" in bijux_proteomics_intelligence.__all__
    assert "ScenarioEvaluation" in bijux_proteomics_intelligence.__all__
    assert "CandidateRejection" in bijux_proteomics_intelligence.__all__


def test_knowledge_public_api_contains_expected_exports() -> None:
    assert "EvidenceClaim" in bijux_proteomics_knowledge.__all__
    assert "ResolutionAction" in bijux_proteomics_knowledge.__all__
    assert "EvidenceGraph" in bijux_proteomics_knowledge.__all__


def test_lab_public_api_contains_expected_exports() -> None:
    assert "ScheduledPlan" in bijux_proteomics_lab.__all__
    assert "AssayOutcome" in bijux_proteomics_lab.__all__
    assert "AssayDependency" in bijux_proteomics_lab.__all__
