# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Parameter parsing, validation, and comparison over search-adapter engines."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterKind,
    SearchConfigValidationIssue,
    SearchConfigValidationReport,
    SearchParameterComparisonReport,
    SearchParameterDifferenceEntry,
    SearchParameterReport,
)
from bijux_proteomics.identification.search_adapters.engines.comet import parse_comet_parameters
from bijux_proteomics.identification.search_adapters.engines.diann import parse_diann_parameters
from bijux_proteomics.identification.search_adapters.engines.maxquant import parse_maxquant_parameters
from bijux_proteomics.identification.search_adapters.engines.msfragger import parse_msfragger_parameters
from bijux_proteomics.identification.search_adapters.engines.sage import parse_sage_parameters
from bijux_proteomics.identification.search_adapters.engines.spectronaut import parse_spectronaut_parameters
from bijux_proteomics.identification.search_adapters.parameter_support import SUPPORTED_ENZYMES


def parse_search_parameter_file(*, source_path: Path, adapter_kind: SearchAdapterKind) -> SearchParameterReport:
    """Parse one supported search-engine parameter file into a stable contract."""
    if adapter_kind is SearchAdapterKind.COMET:
        return parse_comet_parameters(source_path)
    if adapter_kind is SearchAdapterKind.MSFRAGGER:
        return parse_msfragger_parameters(source_path)
    if adapter_kind is SearchAdapterKind.SAGE:
        return parse_sage_parameters(source_path)
    if adapter_kind is SearchAdapterKind.MAXQUANT_EVIDENCE:
        return parse_maxquant_parameters(source_path)
    if adapter_kind is SearchAdapterKind.DIANN:
        return parse_diann_parameters(source_path)
    if adapter_kind is SearchAdapterKind.SPECTRONAUT:
        return parse_spectronaut_parameters(source_path)
    raise ValueError(f"search parameter parsing is not supported for adapter {adapter_kind.value!r}")


def supports_search_parameter_parsing(adapter_kind: SearchAdapterKind) -> bool:
    return adapter_kind in {
        SearchAdapterKind.COMET,
        SearchAdapterKind.MSFRAGGER,
        SearchAdapterKind.SAGE,
        SearchAdapterKind.MAXQUANT_EVIDENCE,
        SearchAdapterKind.DIANN,
        SearchAdapterKind.SPECTRONAUT,
    }


def validate_search_parameters(
    parameters: SearchParameterReport,
) -> SearchConfigValidationReport:
    """Validate one parsed search-engine configuration."""
    issues: list[SearchConfigValidationIssue] = []
    if parameters.enzyme not in SUPPORTED_ENZYMES:
        issues.append(
            SearchConfigValidationIssue(
                code="unknown_enzyme",
                message=f"unsupported enzyme {parameters.enzyme!r}",
                severity="error",
            )
        )
    if not parameters.database_path:
        issues.append(
            SearchConfigValidationIssue(
                code="missing_database_path",
                message="search configuration must declare a database path",
                severity="error",
            )
        )
    if not parameters.has_decoy_strategy:
        issues.append(
            SearchConfigValidationIssue(
                code="missing_decoy_strategy",
                message="search configuration does not declare a decoy prefix or decoy database",
                severity="error",
            )
        )
    if parameters.precursor_tolerance is None or parameters.precursor_tolerance <= 0:
        issues.append(
            SearchConfigValidationIssue(
                code="invalid_precursor_tolerance",
                message="precursor tolerance must be positive",
                severity="error",
            )
        )
    if parameters.fragment_tolerance is None or parameters.fragment_tolerance <= 0:
        issues.append(
            SearchConfigValidationIssue(
                code="invalid_fragment_tolerance",
                message="fragment tolerance must be positive",
                severity="error",
            )
        )
    fixed_by_signature = {
        (definition.site, round(definition.mass_delta, 6))
        for definition in parameters.fixed_modifications
    }
    for definition in parameters.variable_modifications:
        signature = (definition.site, round(definition.mass_delta, 6))
        if signature in fixed_by_signature:
            issues.append(
                SearchConfigValidationIssue(
                    code="overlapping_modification_definition",
                    message=(
                        f"modification {definition.site}@{definition.mass_delta} is both fixed and variable"
                    ),
                    severity="error",
                )
            )
    return SearchConfigValidationReport(
        parameters=parameters,
        valid=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
    )


def _render_parameter_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, tuple):
        return json.dumps(
            [item.to_dict() if hasattr(item, "to_dict") else item for item in value],
            sort_keys=True,
            separators=(",", ":"),
        )
    return str(value)


def compare_search_parameters(
    left: SearchParameterReport,
    right: SearchParameterReport,
) -> SearchParameterComparisonReport:
    """Compare normalized engine parameter reports across runs or engines."""
    comparable = (
        left.adapter_kind is right.adapter_kind
        and left.enzyme == right.enzyme
        and left.precursor_tolerance_unit == right.precursor_tolerance_unit
        and left.fragment_tolerance_unit == right.fragment_tolerance_unit
    )
    differences: list[SearchParameterDifferenceEntry] = []
    for field_name, left_value, right_value, note in (
        (
            "enzyme",
            left.enzyme,
            right.enzyme,
            "digestion enzyme differences alter the search space and are not directly interchangeable",
        ),
        (
            "missed_cleavages",
            left.missed_cleavages,
            right.missed_cleavages,
            "missed-cleavage policy changes the enumerated peptide space",
        ),
        (
            "precursor_tolerance",
            left.precursor_tolerance,
            right.precursor_tolerance,
            "precursor tolerance differences change precursor matching strictness",
        ),
        (
            "precursor_tolerance_unit",
            left.precursor_tolerance_unit,
            right.precursor_tolerance_unit,
            "precursor tolerance units must be aligned before comparing parameter strictness",
        ),
        (
            "fragment_tolerance",
            left.fragment_tolerance,
            right.fragment_tolerance,
            "fragment tolerance differences change fragment matching strictness",
        ),
        (
            "fragment_tolerance_unit",
            left.fragment_tolerance_unit,
            right.fragment_tolerance_unit,
            "fragment tolerance units must be aligned before comparing parameter strictness",
        ),
        (
            "database_path",
            left.database_path,
            right.database_path,
            "database path differences may indicate distinct search databases",
        ),
        (
            "decoy_prefix",
            left.decoy_prefix,
            right.decoy_prefix,
            "decoy-prefix differences change decoy interpretation and downstream FDR expectations",
        ),
        (
            "fixed_modifications",
            left.fixed_modifications,
            right.fixed_modifications,
            "fixed modification differences change the assumed peptide masses",
        ),
        (
            "variable_modifications",
            left.variable_modifications,
            right.variable_modifications,
            "variable modification differences change the allowed search hypotheses",
        ),
    ):
        rendered_left = _render_parameter_value(left_value)
        rendered_right = _render_parameter_value(right_value)
        differences.append(
            SearchParameterDifferenceEntry(
                field_name=field_name,
                left_value=rendered_left,
                right_value=rendered_right,
                severity="compatible"
                if rendered_left == rendered_right
                else "different",
                note=note,
            )
        )
    return SearchParameterComparisonReport(
        left_adapter_kind=left.adapter_kind,
        right_adapter_kind=right.adapter_kind,
        left_adapter_name=left.adapter_name,
        right_adapter_name=right.adapter_name,
        comparable=comparable,
        differences=tuple(differences),
    )
