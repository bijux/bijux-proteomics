# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Comet search-adapter ownership."""

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


COMET_ENZYME_BY_NUMBER = {
    "0": "no_enzyme",
    "1": "trypsin",
    "2": "trypsin/p",
    "3": "lys-c",
    "4": "lys-n",
    "5": "arg-c",
    "6": "asp-n",
    "8": "glu-c",
}

COMET_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.COMET,
    display_name="Comet",
    description="Normalize Comet-like tabular search outputs into stable PSM records.",
    score_orientation=ScoreOrientation.LOWER_BETTER,
    score_family=SearchScoreFamily.EXPECTATION_VALUE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan",
        "plain_peptide",
        "charge",
        "expect",
        "protein",
        "target_decoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan",
        peptide="plain_peptide",
        charge="charge",
        score="expect",
        protein_refs="protein",
        decoy_label="target_decoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("decoy", "true", "1"),
        explicit_target_values=("target", "false", "0"),
    ),
    supported_extensions=(".txt", ".tsv"),
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=True,
)

COMET_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.COMET,
    dialect_id="pipeline-export",
    display_name="Comet pipeline export",
    description="Normalize a Comet-like pipeline export with renamed expectation columns.",
    score_family=SearchScoreFamily.EXPECTATION_VALUE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan_num",
        "peptide_sequence",
        "precursor_charge",
        "expectation_value",
        "protein_ids",
        "is_decoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan_num",
        peptide="peptide_sequence",
        charge="precursor_charge",
        score="expectation_value",
        protein_refs="protein_ids",
        decoy_label="is_decoy",
        protein_separator=";",
    ),
)

COMET_PSM_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.COMET,
    dialect_id="comet-psm",
    display_name="Comet psm export",
    description="Normalize a realistic Comet tabular export into stable PSM records.",
    score_family=SearchScoreFamily.EXPECTATION_VALUE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan",
        "plain_peptide",
        "modified_peptide",
        "charge",
        "expect",
        "xcorr",
        "delta_cn",
        "sp_score",
        "protein",
        "target_decoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan",
        peptide="plain_peptide",
        charge="charge",
        score="expect",
        protein_refs="protein",
        decoy_label="target_decoy",
        protein_separator=";",
    ),
)

COMET_DIALECTS = (COMET_PIPELINE_DIALECT, COMET_PSM_DIALECT)

def parse_comet_parameters(path: Path) -> SearchParameterReport:
    fields = parse_key_value_parameters(path)
    precursor_units = (
        SearchToleranceUnit.PPM
        if fields.get("peptide_mass_units") == "2"
        else SearchToleranceUnit.DA
    )
    enzyme = COMET_ENZYME_BY_NUMBER.get(
        fields.get("search_enzyme_number", "").strip(),
        fields.get("search_enzyme_name", "unknown").strip().lower(),
    )
    database_path = fields.get("database_name")
    decoy_search = fields.get("decoy_search", "0").strip() in {"1", "true", "yes"}
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.COMET,
        adapter_name="Comet",
        enzyme=enzyme,
        missed_cleavages=int(fields["allowed_missed_cleavage"])
        if fields.get("allowed_missed_cleavage")
        else None,
        precursor_tolerance=float(fields["peptide_mass_tolerance"])
        if fields.get("peptide_mass_tolerance")
        else None,
        precursor_tolerance_unit=precursor_units,
        fragment_tolerance=float(fields["fragment_bin_tol"])
        if fields.get("fragment_bin_tol")
        else None,
        fragment_tolerance_unit=SearchToleranceUnit.DA
        if fields.get("fragment_bin_tol")
        else None,
        database_path=database_path,
        decoy_prefix="DECOY_" if decoy_search else None,
        has_decoy_strategy=decoy_search
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_modifications_from_fields(fields),
        variable_modifications=variable_modifications_from_key_value_fields(fields),
        raw_fields=fields,
    )

def build_comet_output_corpus_report(corpus_root: Path) -> "SearchEngineCorpusReport":
    """Build corpus coverage over Comet native and pipeline-like outputs."""
    from ..corpus import (
        SearchCorpusInputSpecification,
        build_search_engine_corpus_report,
    )

    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.COMET,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.COMET,
                dialect_id="default",
                result_file="comet_results.tsv",
                config_file="comet.params",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.COMET,
                dialect_id="pipeline-export",
                result_file="comet_pipeline_export.tsv",
                config_file="comet.params",
            ),
        ),
    )
