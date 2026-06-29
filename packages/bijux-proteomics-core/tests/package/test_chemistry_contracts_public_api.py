# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import contracts

EXPECTED_CHEMISTRY_CONTRACT_EXPORTS = (
    "AppliedModification",
    "FragmentIon",
    "FragmentIonSeries",
    "FragmentIonShiftValidationEntry",
    "FragmentIonShiftValidationReport",
    "IsotopeEnvelopeStatus",
    "IsotopePeak",
    "IsotopicLabelingPolicy",
    "MassType",
    "ModificationLocalizationAdvisory",
    "ModificationLocalizationCandidate",
    "ModificationLocalizationState",
    "ModificationLocalizationStatus",
    "ModificationPosition",
    "ModificationProvenance",
    "ModificationRegistryDocument",
    "ModificationRegistryValidationIssue",
    "ModificationRegistryValidationReport",
    "ModificationSiteValidationIssue",
    "ModificationSiteValidationReport",
    "ModifiedPeptideExportRecord",
    "NeutralLoss",
    "ParsedModifiedPeptide",
    "PeptideChargeState",
    "PeptideIsotopeEnvelope",
    "StaticModification",
    "VariableModification",
    "VariableModificationEnumerationEntry",
    "VariableModificationEnumerationReport",
    "approximate_peptide_isotope_envelope",
    "build_modification_localization_advisory",
    "build_modification_registry",
    "build_modified_peptide",
    "build_modified_peptide_export_record",
    "build_peptide_charge_state",
    "calculate_average_peptide_mass",
    "calculate_fragment_ions",
    "calculate_modified_peptide_mass",
    "calculate_monoisotopic_peptide_mass",
    "calculate_peptide_mz",
    "canonicalize_modified_peptide",
    "enumerate_variable_modifications",
    "export_modified_peptides_jsonl",
    "export_modified_peptides_tsv",
    "get_modification",
    "load_modification_registry",
    "modification_registry",
    "parse_modified_peptide",
    "validate_modification_registry",
    "validate_modified_peptide_fragment_ions",
    "validate_modified_peptide_sites",
)

UNWANTED_CHEMISTRY_CONTRACT_EXPORTS = {
    "annotations",
    "calculate_sequence_average_mass",
    "calculate_sequence_monoisotopic_mass",
    "fragment_ions",
    "mass_projection",
    "models",
    "modified_peptides",
    "registry_access",
    "registry_lookup",
    "resolve_modification_definition",
}


def test_chemistry_contracts_public_api_is_explicit_and_curated() -> None:
    assert tuple(contracts.__all__) == EXPECTED_CHEMISTRY_CONTRACT_EXPORTS
    assert UNWANTED_CHEMISTRY_CONTRACT_EXPORTS.isdisjoint(contracts.__all__)
