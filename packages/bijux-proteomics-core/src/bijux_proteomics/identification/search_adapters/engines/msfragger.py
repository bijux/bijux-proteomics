# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""MSFragger and FragPipe search-adapter ownership."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bijux_proteomics.identification.contracts import (
    SearchResultColumnMapping,
    TargetDecoyLabelPolicy,
)

from ..contracts import (
    ScoreOrientation,
    SearchAdapterDialectManifest,
    SearchAdapterKind,
    SearchAdapterManifest,
    SearchParameterReport,
    SearchResultFamily,
    SearchScoreFamily,
    SearchToleranceUnit,
)
from ..parameter_support import (
    fixed_modifications_from_fields,
    parse_key_value_parameters,
    variable_modifications_from_key_value_fields,
)

if TYPE_CHECKING:
    from ..corpus import SearchEngineCorpusReport


MSFRAGGER_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.MSFRAGGER,
    display_name="MSFragger",
    description="Normalize MSFragger-like tabular search outputs into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    score_family=SearchScoreFamily.HYPERSCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "Spectrum",
        "Peptide",
        "Charge",
        "Hyperscore",
        "Protein",
        "IsDecoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="Spectrum",
        peptide="Peptide",
        charge="Charge",
        score="Hyperscore",
        protein_refs="Protein",
        decoy_label="IsDecoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("1", "decoy", "true"),
        explicit_target_values=("0", "target", "false"),
    ),
    supported_extensions=(".tsv",),
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=True,
)

MSFRAGGER_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.MSFRAGGER,
    dialect_id="pipeline-export",
    display_name="MSFragger pipeline export",
    description="Normalize an MSFragger-like pipeline export with renamed hyperscore fields.",
    score_family=SearchScoreFamily.HYPERSCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "spectrum_key",
        "plain_peptide",
        "precursor_charge",
        "hyperscore_value",
        "proteins_joined",
        "decoy_state",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="spectrum_key",
        peptide="plain_peptide",
        charge="precursor_charge",
        score="hyperscore_value",
        protein_refs="proteins_joined",
        decoy_label="decoy_state",
        protein_separator=";",
    ),
)

FRAGPIPE_PSM_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.MSFRAGGER,
    dialect_id="fragpipe-psm",
    display_name="FragPipe psm export",
    description="Normalize a FragPipe psm.tsv export into stable PSM records.",
    score_family=SearchScoreFamily.HYPERSCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "Spectrum",
        "Spectrum File",
        "Peptide",
        "Modified Peptide",
        "Charge",
        "Hyperscore",
        "Intensity",
        "Protein",
        "IsDecoy",
        "QValue",
        "Assigned Modifications",
        "Observed Modifications",
        "Mass Difference",
    ),
    mapping=SearchResultColumnMapping(
        run_id="Spectrum File",
        spectrum_id="Spectrum",
        peptide="Peptide",
        charge="Charge",
        score="Hyperscore",
        intensity="Intensity",
        protein_refs="Protein",
        q_value="QValue",
        decoy_label="IsDecoy",
        protein_separator=";",
    ),
)

MSFRAGGER_DIALECTS = (MSFRAGGER_PIPELINE_DIALECT, FRAGPIPE_PSM_DIALECT)


def parse_msfragger_parameters(path: Path) -> SearchParameterReport:
    fields = parse_key_value_parameters(path)
    precursor_unit = (
        SearchToleranceUnit.PPM
        if fields.get("precursor_mass_units") == "1"
        else SearchToleranceUnit.DA
    )
    fragment_unit = (
        SearchToleranceUnit.PPM
        if fields.get("fragment_mass_units") == "1"
        else SearchToleranceUnit.DA
    )
    lower = (
        abs(float(fields["precursor_mass_lower"]))
        if fields.get("precursor_mass_lower")
        else None
    )
    upper = (
        abs(float(fields["precursor_mass_upper"]))
        if fields.get("precursor_mass_upper")
        else None
    )
    precursor_tolerance = (
        max(lower or 0.0, upper or 0.0)
        if lower is not None or upper is not None
        else None
    )
    database_path = fields.get("database_name")
    decoy_prefix = fields.get("decoy_prefix")
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        adapter_name="MSFragger",
        enzyme=fields.get("search_enzyme_name", "unknown").strip().lower(),
        missed_cleavages=int(fields["allowed_missed_cleavage"])
        if fields.get("allowed_missed_cleavage")
        else None,
        precursor_tolerance=precursor_tolerance,
        precursor_tolerance_unit=precursor_unit
        if precursor_tolerance is not None
        else None,
        fragment_tolerance=float(fields["fragment_mass_tolerance"])
        if fields.get("fragment_mass_tolerance")
        else None,
        fragment_tolerance_unit=fragment_unit
        if fields.get("fragment_mass_tolerance")
        else None,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_modifications_from_fields(fields),
        variable_modifications=variable_modifications_from_key_value_fields(fields),
        raw_fields=fields,
    )


def build_msfragger_output_corpus_report(
    corpus_root: Path,
) -> SearchEngineCorpusReport:
    """Build corpus coverage over MSFragger native and pipeline-like outputs."""
    from ..corpus import (
        SearchCorpusInputSpecification,
        build_search_engine_corpus_report,
    )

    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.MSFRAGGER,
                dialect_id="default",
                result_file="msfragger_results.tsv",
                config_file="msfragger.params",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.MSFRAGGER,
                dialect_id="pipeline-export",
                result_file="msfragger_pipeline_export.tsv",
                config_file="msfragger.params",
            ),
        ),
    )
