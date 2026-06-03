# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""DIA-NN search-adapter ownership."""

from __future__ import annotations

import json
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
from ..parameter_support import modification_definitions_from_compact_value

if TYPE_CHECKING:
    from ..corpus import SearchEngineCorpusReport


DIANN_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.DIANN,
    display_name="DIA-NN",
    description="Normalize DIA-NN report-style tables into stable PSM-like records.",
    score_orientation=ScoreOrientation.LOWER_BETTER,
    score_family=SearchScoreFamily.Q_VALUE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "Precursor.Id",
        "Stripped.Sequence",
        "Precursor.Charge",
        "Q.Value",
        "Protein.Ids",
        "Decoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="Precursor.Id",
        peptide="Stripped.Sequence",
        charge="Precursor.Charge",
        score="Q.Value",
        protein_refs="Protein.Ids",
        q_value="Q.Value",
        decoy_label="Decoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("1", "true", "decoy"),
        explicit_target_values=("0", "false", "target"),
    ),
    supported_extensions=(".tsv",),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=False,
)

DIANN_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.DIANN,
    dialect_id="pipeline-export",
    display_name="DIA-NN pipeline export",
    description="Normalize a DIA-NN-like pipeline export with simplified report columns.",
    score_family=SearchScoreFamily.Q_VALUE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "precursor_id",
        "sequence",
        "charge",
        "qvalue",
        "protein_ids",
        "decoy_flag",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="precursor_id",
        peptide="sequence",
        charge="charge",
        score="qvalue",
        protein_refs="protein_ids",
        q_value="qvalue",
        decoy_label="decoy_flag",
        protein_separator=";",
    ),
)

DIANN_DIALECTS = (DIANN_PIPELINE_DIALECT,)


def parse_diann_parameters(path: Path) -> SearchParameterReport:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("dia-nn parameter payload must be a JSON object")
    fixed_modifications = modification_definitions_from_compact_value(
        str(payload.get("fixed_modifications", "")),
        variable=False,
        source_key="fixed_modifications",
    )
    variable_modifications = modification_definitions_from_compact_value(
        str(payload.get("variable_modifications", "")),
        variable=True,
        source_key="variable_modifications",
    )
    database_path = (
        str(payload.get("fasta_file", "")).strip()
        or str(payload.get("library_file", "")).strip()
        or None
    )
    decoy_prefix = str(payload.get("decoy_prefix", "")).strip() or None
    precursor_value = payload.get("precursor_tolerance_ppm")
    fragment_value = payload.get("fragment_tolerance_ppm")
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.DIANN,
        adapter_name="DIA-NN",
        enzyme=str(payload.get("enzyme", "unspecific")).strip().lower(),
        missed_cleavages=int(payload["max_missed_cleavages"])
        if payload.get("max_missed_cleavages") is not None
        else None,
        precursor_tolerance=float(precursor_value)
        if precursor_value is not None
        else None,
        precursor_tolerance_unit=SearchToleranceUnit.PPM
        if precursor_value is not None
        else None,
        fragment_tolerance=float(fragment_value)
        if fragment_value is not None
        else None,
        fragment_tolerance_unit=SearchToleranceUnit.PPM
        if fragment_value is not None
        else None,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_modifications,
        variable_modifications=variable_modifications,
        raw_fields={
            key: json.dumps(value, sort_keys=True)
            for key, value in sorted(payload.items())
        },
    )


def build_diann_output_corpus_report(corpus_root: Path) -> SearchEngineCorpusReport:
    """Build corpus coverage over DIA-NN report and pipeline-like exports."""
    from ..corpus import (
        SearchCorpusInputSpecification,
        build_search_engine_corpus_report,
    )

    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.DIANN,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.DIANN,
                dialect_id="default",
                result_file="diann_report.tsv",
                config_file="diann_config.json",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.DIANN,
                dialect_id="pipeline-export",
                result_file="diann_pipeline_export.tsv",
                config_file="diann_config.json",
            ),
        ),
    )
