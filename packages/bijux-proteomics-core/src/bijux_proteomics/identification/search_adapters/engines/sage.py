# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Sage search-adapter ownership."""

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
    SearchModificationDefinition,
    SearchParameterReport,
    SearchResultFamily,
    SearchScoreFamily,
    SearchToleranceUnit,
)

if TYPE_CHECKING:
    from ..corpus import SearchEngineCorpusReport


SAGE_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.SAGE,
    display_name="Sage",
    description="Normalize Sage-like tabular search outputs into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    score_family=SearchScoreFamily.DISCRIMINANT_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scannr",
        "peptide",
        "charge",
        "discriminant_score",
        "proteins",
        "label",
        "q_value",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scannr",
        peptide="peptide",
        charge="charge",
        score="discriminant_score",
        protein_refs="proteins",
        q_value="q_value",
        decoy_label="label",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("decoy", "-1", "1"),
        explicit_target_values=("target", "1", "0"),
    ),
    supported_extensions=(".tsv",),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=True,
)

SAGE_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.SAGE,
    dialect_id="pipeline-export",
    display_name="Sage pipeline export",
    description="Normalize a Sage-like pipeline export with renamed score fields.",
    score_family=SearchScoreFamily.DISCRIMINANT_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan_id",
        "stripped_peptide",
        "precursor_charge",
        "score_discriminant",
        "protein_group",
        "decoy_flag",
        "qvalue",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan_id",
        peptide="stripped_peptide",
        charge="precursor_charge",
        score="score_discriminant",
        protein_refs="protein_group",
        q_value="qvalue",
        decoy_label="decoy_flag",
        protein_separator=";",
    ),
)

SAGE_PSM_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.SAGE,
    dialect_id="sage-psm",
    display_name="Sage psm export",
    description="Normalize a realistic Sage PSM export into stable PSM records.",
    score_family=SearchScoreFamily.DISCRIMINANT_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "filename",
        "scannr",
        "peptide",
        "charge",
        "discriminant_score",
        "hyperscore",
        "proteins",
        "label",
        "q_value",
        "peptide_q_value",
        "protein_q_value",
        "posterior_error",
        "matched_peaks",
        "longest_b",
        "longest_y",
        "matched_intensity_pct",
        "precursor_ppm",
        "fragment_ppm",
        "isotope_error",
        "rt",
        "aligned_rt",
        "predicted_rt",
        "delta_rt_model",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scannr",
        peptide="peptide",
        charge="charge",
        score="discriminant_score",
        protein_refs="proteins",
        q_value="q_value",
        decoy_label="label",
        protein_separator=";",
    ),
)

SAGE_DIALECTS = (SAGE_PIPELINE_DIALECT, SAGE_PSM_DIALECT)


def parse_sage_parameters(path: Path) -> SearchParameterReport:
    payload = json.loads(path.read_text())
    enzyme_payload = payload.get("enzyme", {})
    database_payload = payload.get("database", {})
    precursor_payload = payload.get("precursor_tol", {})
    fragment_payload = payload.get("fragment_tol", {})
    mods_payload = payload.get("mods", {})

    enzyme_name = (
        str(enzyme_payload).strip().lower()
        if isinstance(enzyme_payload, str)
        else str(enzyme_payload.get("name", "unknown")).strip().lower()
    )
    missed_cleavages = (
        payload.get("missed_cleavages")
        if isinstance(enzyme_payload, str)
        else enzyme_payload.get("missed_cleavages")
    )
    precursor_value = None
    precursor_unit = None
    if isinstance(precursor_payload, dict) and precursor_payload:
        precursor_unit = (
            SearchToleranceUnit.PPM
            if "ppm" in precursor_payload
            else SearchToleranceUnit.DA
            if "da" in precursor_payload
            else None
        )
        precursor_value = precursor_payload.get("ppm", precursor_payload.get("da"))
    elif payload.get("precursor_tol_ppm") is not None:
        precursor_unit = SearchToleranceUnit.PPM
        precursor_value = payload.get("precursor_tol_ppm")
    elif payload.get("precursor_tol_da") is not None:
        precursor_unit = SearchToleranceUnit.DA
        precursor_value = payload.get("precursor_tol_da")

    fragment_value = None
    fragment_unit = None
    if isinstance(fragment_payload, dict) and fragment_payload:
        fragment_unit = (
            SearchToleranceUnit.PPM
            if "ppm" in fragment_payload
            else SearchToleranceUnit.DA
            if "da" in fragment_payload
            else None
        )
        fragment_value = fragment_payload.get("ppm", fragment_payload.get("da"))
    elif payload.get("fragment_tol_ppm") is not None:
        fragment_unit = SearchToleranceUnit.PPM
        fragment_value = payload.get("fragment_tol_ppm")
    elif payload.get("fragment_tol_da") is not None:
        fragment_unit = SearchToleranceUnit.DA
        fragment_value = payload.get("fragment_tol_da")

    def _mass_delta_for_named_modification(name: str) -> float:
        known = {
            "acetyl": 42.010565,
            "carbamidomethyl": 57.021464,
            "oxidation": 15.994915,
            "phospho": 79.966331,
        }
        return known.get(name.strip().lower(), 0.0)

    def _compact_sage_modifications(
        values: object,
        *,
        variable: bool,
        prefix: str,
    ) -> tuple[SearchModificationDefinition, ...]:
        if not isinstance(values, list):
            return ()
        definitions: list[SearchModificationDefinition] = []
        for token in values:
            if not isinstance(token, str) or "@" not in token:
                continue
            name, residues = token.split("@", 1)
            mass_delta = _mass_delta_for_named_modification(name)
            for residue in residues:
                definitions.append(
                    SearchModificationDefinition(
                        site=residue.upper(),
                        mass_delta=mass_delta,
                        variable=variable,
                        source_key=f"{prefix}.{name}@{residue.upper()}",
                    )
                )
        return tuple(definitions)

    fixed_definitions = tuple(
        SearchModificationDefinition(
            site=str(site).upper(),
            mass_delta=float(mass_delta),
            variable=False,
            source_key=f"mods.static.{site}",
        )
        for site, mass_delta in sorted(
            (mods_payload.get("static") or {}).items()
            if isinstance(mods_payload, dict)
            else {}
        )
    )
    variable_definitions = tuple(
        SearchModificationDefinition(
            site=str(site).upper(),
            mass_delta=float(mass_delta),
            variable=True,
            source_key=f"mods.variable.{site}",
        )
        for site, deltas in sorted(
            (mods_payload.get("variable") or {}).items()
            if isinstance(mods_payload, dict)
            else {}
        )
        for mass_delta in deltas
    )
    if not fixed_definitions:
        fixed_definitions = _compact_sage_modifications(
            payload.get("fixed_modifications"),
            variable=False,
            prefix="fixed_modifications",
        )
    if not variable_definitions:
        variable_definitions = _compact_sage_modifications(
            payload.get("variable_modifications"),
            variable=True,
            prefix="variable_modifications",
        )
    database_path = (
        database_payload.get("fasta")
        if isinstance(database_payload, dict)
        else payload.get("database_path")
    )
    decoy_prefix = (
        database_payload.get("decoy_tag")
        if isinstance(database_payload, dict)
        else payload.get("decoy_prefix")
    )
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.SAGE,
        adapter_name="Sage",
        enzyme=enzyme_name,
        missed_cleavages=int(missed_cleavages)
        if missed_cleavages is not None
        else None,
        precursor_tolerance=float(precursor_value)
        if precursor_unit is not None and precursor_value is not None
        else None,
        precursor_tolerance_unit=precursor_unit,
        fragment_tolerance=float(fragment_value)
        if fragment_unit is not None and fragment_value is not None
        else None,
        fragment_tolerance_unit=fragment_unit,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_definitions,
        variable_modifications=variable_definitions,
        raw_fields={
            key: json.dumps(value, sort_keys=True)
            for key, value in sorted(payload.items())
        },
    )


def build_sage_output_corpus_report(corpus_root: Path) -> SearchEngineCorpusReport:
    """Build corpus coverage over Sage native and pipeline-like outputs."""
    from ..corpus import (
        SearchCorpusInputSpecification,
        build_search_engine_corpus_report,
    )

    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.SAGE,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.SAGE,
                dialect_id="default",
                result_file="sage_results.tsv",
                config_file="sage_search.json",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.SAGE,
                dialect_id="pipeline-export",
                result_file="sage_pipeline_export.tsv",
                config_file="sage_search.json",
            ),
        ),
    )
