# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Spectronaut search-adapter ownership."""

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
from ..parameter_support import modification_definitions_from_compact_value, parse_key_value_parameters

if TYPE_CHECKING:
    from ..corpus import SearchEngineCorpusReport


SPECTRONAUT_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.SPECTRONAUT,
    display_name="Spectronaut",
    description="Normalize Spectronaut-like tables into stable PSM-like records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    score_family=SearchScoreFamily.CONFIDENCE_SCORE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "EG.PrecursorId",
        "PEP.StrippedSequence",
        "FG.Charge",
        "EG.Cscore",
        "PG.ProteinAccessions",
        "EG.IsDecoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="EG.PrecursorId",
        peptide="PEP.StrippedSequence",
        charge="FG.Charge",
        score="EG.Cscore",
        protein_refs="PG.ProteinAccessions",
        decoy_label="EG.IsDecoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("true", "1", "decoy"),
        explicit_target_values=("false", "0", "target"),
    ),
    supported_extensions=(".tsv",),
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=False,
)

SPECTRONAUT_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.SPECTRONAUT,
    dialect_id="pipeline-export",
    display_name="Spectronaut pipeline export",
    description="Normalize a Spectronaut-like pipeline export with simplified precursor columns.",
    score_family=SearchScoreFamily.CONFIDENCE_SCORE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "precursor_key",
        "stripped_sequence",
        "charge",
        "cscore_value",
        "protein_accessions",
        "decoy_flag",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="precursor_key",
        peptide="stripped_sequence",
        charge="charge",
        score="cscore_value",
        protein_refs="protein_accessions",
        decoy_label="decoy_flag",
        protein_separator=";",
    ),
)

SPECTRONAUT_REVIEW_REPORT_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.SPECTRONAUT,
    dialect_id="review-report",
    display_name="Spectronaut review report",
    description="Normalize a Spectronaut export that preserves q-value alongside the confidence score.",
    score_family=SearchScoreFamily.CONFIDENCE_SCORE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "EG.PrecursorId",
        "PEP.StrippedSequence",
        "FG.LabeledSequence",
        "FG.Charge",
        "EG.Cscore",
        "EG.Qvalue",
        "PG.ProteinGroups",
        "PG.ProteinAccessions",
        "R.FileName",
        "R.Condition",
        "FG.Quantity",
        "PG.Quantity",
        "EG.IsDecoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="EG.PrecursorId",
        peptide="PEP.StrippedSequence",
        charge="FG.Charge",
        score="EG.Cscore",
        protein_refs="PG.ProteinAccessions",
        q_value="EG.Qvalue",
        decoy_label="EG.IsDecoy",
        protein_separator=";",
    ),
)

SPECTRONAUT_DIALECTS = (
    SPECTRONAUT_PIPELINE_DIALECT,
    SPECTRONAUT_REVIEW_REPORT_DIALECT,
)

def parse_spectronaut_parameters(path: Path) -> SearchParameterReport:
    fields = parse_key_value_parameters(path)
    fixed_modifications = modification_definitions_from_compact_value(
        fields.get("fixed_modifications"),
        variable=False,
        source_key="fixed_modifications",
    )
    variable_modifications = modification_definitions_from_compact_value(
        fields.get("variable_modifications"),
        variable=True,
        source_key="variable_modifications",
    )
    database_path = fields.get("library_file") or fields.get("fasta_file") or None
    decoy_prefix = fields.get("decoy_prefix")
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.SPECTRONAUT,
        adapter_name="Spectronaut",
        enzyme=fields.get("digestion_enzyme", "unknown").strip().lower(),
        missed_cleavages=int(fields["max_missed_cleavages"])
        if fields.get("max_missed_cleavages")
        else None,
        precursor_tolerance=float(fields["precursor_tolerance_ppm"])
        if fields.get("precursor_tolerance_ppm")
        else None,
        precursor_tolerance_unit=SearchToleranceUnit.PPM
        if fields.get("precursor_tolerance_ppm")
        else None,
        fragment_tolerance=float(fields["fragment_tolerance_ppm"])
        if fields.get("fragment_tolerance_ppm")
        else None,
        fragment_tolerance_unit=SearchToleranceUnit.PPM
        if fields.get("fragment_tolerance_ppm")
        else None,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_modifications,
        variable_modifications=variable_modifications,
        raw_fields=fields,
    )

def build_spectronaut_output_corpus_report(
    corpus_root: Path,
) -> "SearchEngineCorpusReport":
    """Build corpus coverage over Spectronaut-like native and pipeline exports."""
    from ..corpus import (
        SearchCorpusInputSpecification,
        build_search_engine_corpus_report,
    )

    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.SPECTRONAUT,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.SPECTRONAUT,
                dialect_id="default",
                result_file="spectronaut_report.tsv",
                config_file="spectronaut_settings.txt",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.SPECTRONAUT,
                dialect_id="pipeline-export",
                result_file="spectronaut_pipeline_export.tsv",
                config_file="spectronaut_settings.txt",
            ),
        ),
    )
