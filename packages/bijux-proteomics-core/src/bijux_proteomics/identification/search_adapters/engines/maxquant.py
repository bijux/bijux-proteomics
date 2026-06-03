# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""MaxQuant search-adapter ownership."""

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
    modification_definitions_from_compact_value,
    parse_key_value_parameters,
)

if TYPE_CHECKING:
    from ..corpus import SearchEngineCorpusReport


MAXQUANT_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
    display_name="MaxQuant evidence",
    description="Normalize MaxQuant evidence-like tables into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    score_family=SearchScoreFamily.ENGINE_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "MS/MS scan number",
        "Modified sequence",
        "Charge",
        "Score",
        "Proteins",
        "Reverse",
        "PEP",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="MS/MS scan number",
        peptide="Modified sequence",
        charge="Charge",
        score="Score",
        protein_refs="Proteins",
        posterior_error_probability="PEP",
        decoy_label="Reverse",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="REV__",
        explicit_decoy_values=("+", "decoy", "true", "1"),
        explicit_target_values=("", "target", "false", "0"),
    ),
    supported_extensions=(".txt", ".tsv"),
    supports_q_value=False,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=False,
)

MAXQUANT_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
    dialect_id="pipeline-export",
    display_name="MaxQuant pipeline export",
    description="Normalize a MaxQuant-like pipeline export with simplified evidence columns.",
    score_family=SearchScoreFamily.ENGINE_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan_number",
        "sequence_with_mods",
        "precursor_charge",
        "score_value",
        "leading_proteins",
        "reverse_flag",
        "pep_value",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan_number",
        peptide="sequence_with_mods",
        charge="precursor_charge",
        score="score_value",
        protein_refs="leading_proteins",
        posterior_error_probability="pep_value",
        decoy_label="reverse_flag",
        protein_separator=";",
    ),
)

MAXQUANT_BUNDLE_EVIDENCE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
    dialect_id="bundle-evidence",
    display_name="MaxQuant bundle evidence",
    description="Normalize a native MaxQuant evidence table by stripped sequence while preserving modified notation in the raw row.",
    score_family=SearchScoreFamily.ENGINE_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "MS/MS scan number",
        "Sequence",
        "Modified sequence",
        "Charge",
        "Score",
        "Proteins",
        "Reverse",
        "PEP",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="MS/MS scan number",
        peptide="Sequence",
        charge="Charge",
        score="Score",
        protein_refs="Proteins",
        posterior_error_probability="PEP",
        decoy_label="Reverse",
        protein_separator=";",
    ),
)

MAXQUANT_DIALECTS = (MAXQUANT_PIPELINE_DIALECT, MAXQUANT_BUNDLE_EVIDENCE_DIALECT)


def parse_maxquant_parameters(path: Path) -> SearchParameterReport:
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
    database_path = fields.get("fasta_file")
    decoy_prefix = fields.get("decoy_prefix", "REV__").strip() or None
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
        adapter_name="MaxQuant evidence",
        enzyme=fields.get("enzyme", "unknown").strip().lower(),
        missed_cleavages=int(fields["max_missed_cleavages"])
        if fields.get("max_missed_cleavages")
        else None,
        precursor_tolerance=float(fields["precursor_tolerance_ppm"])
        if fields.get("precursor_tolerance_ppm")
        else None,
        precursor_tolerance_unit=SearchToleranceUnit.PPM
        if fields.get("precursor_tolerance_ppm")
        else None,
        fragment_tolerance=float(fields["fragment_tolerance_da"])
        if fields.get("fragment_tolerance_da")
        else None,
        fragment_tolerance_unit=SearchToleranceUnit.DA
        if fields.get("fragment_tolerance_da")
        else None,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_modifications,
        variable_modifications=variable_modifications,
        raw_fields=fields,
    )


def build_maxquant_output_corpus_report(
    corpus_root: Path,
) -> SearchEngineCorpusReport:
    """Build corpus coverage over MaxQuant evidence native and pipeline-like outputs."""
    from ..corpus import (
        SearchCorpusInputSpecification,
        build_search_engine_corpus_report,
    )

    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
                dialect_id="default",
                result_file="maxquant_evidence.tsv",
                config_file="maxquant_settings.txt",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
                dialect_id="pipeline-export",
                result_file="maxquant_pipeline_export.tsv",
                config_file="maxquant_settings.txt",
            ),
        ),
    )
