# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Design-validation and multiple-testing benchmark builders."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
from bijux_proteomics.quantification.provenance.review.models import (
    DifferentialAbundanceDesignIssue,
    DifferentialAbundanceDesignValidationReport,
    MultipleTestingScopeBenchmarkEntry,
    MultipleTestingScopeBenchmarkReport,
    MultipleTestingScopeBenchmarkStatus,
)
from bijux_proteomics.quantification.statistics import (
    apply_benjamini_hochberg,
    build_differential_abundance_report,
)
from bijux_proteomics.study.replicate_structure import (
    count_effective_statistical_units_by_condition,
)


def validate_differential_abundance_design_context(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    contrasts: tuple[tuple[str, str], ...],
    covariates: tuple[str, ...] = (),
    blocking_field: str | None = "batch",
    min_replicates_per_condition: int = 2,
    multiple_testing_scope: str = "global_per_analysis",
) -> DifferentialAbundanceDesignValidationReport:
    """Validate DA design assumptions before running statistical comparisons."""
    condition_replicates = count_effective_statistical_units_by_condition(
        design_entries
    )
    issues: list[DifferentialAbundanceDesignIssue] = []
    known_conditions = set(condition_replicates)
    for left, right in contrasts:
        if left == right:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="degenerate_contrast",
                    message=f"contrast {left} vs {right} is degenerate",
                    severity="error",
                )
            )
        missing = [
            condition
            for condition in (left, right)
            if condition not in known_conditions
        ]
        if missing:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="unknown_contrast_condition",
                    message=f"contrast references unknown conditions: {', '.join(missing)}",
                    severity="error",
                )
            )
    for condition, replicate_count in sorted(condition_replicates.items()):
        if replicate_count < min_replicates_per_condition:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="insufficient_replicates",
                    message=(
                        f"condition {condition} has {replicate_count} replicates; "
                        f"minimum is {min_replicates_per_condition}"
                    ),
                    severity="error",
                )
            )
    covariate_lookup = {
        "batch": lambda entry: entry.batch,
        "instrument": lambda entry: entry.instrument,
        "fraction": lambda entry: entry.fraction,
        "replicate": lambda entry: entry.replicate,
    }
    for covariate in covariates:
        resolver = covariate_lookup.get(covariate)
        if resolver is None:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="unknown_covariate",
                    message=f"covariate {covariate!r} is not recognized",
                    severity="warning",
                )
            )
            continue
        values = [resolver(entry) for entry in design_entries]
        if all(value in (None, "", 0) for value in values):
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="empty_covariate",
                    message=f"covariate {covariate!r} has no populated values",
                    severity="warning",
                )
            )
    if blocking_field:
        resolver = covariate_lookup.get(blocking_field)
        if resolver is None:
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="unknown_blocking_field",
                    message=f"blocking field {blocking_field!r} is not recognized",
                    severity="warning",
                )
            )
        elif all(resolver(entry) in (None, "", 0) for entry in design_entries):
            issues.append(
                DifferentialAbundanceDesignIssue(
                    code="missing_blocking_values",
                    message=f"blocking field {blocking_field!r} has no populated values",
                    severity="warning",
                )
            )
    if multiple_testing_scope not in {
        "global_per_analysis",
        "per_contrast",
        "hierarchical",
    }:
        issues.append(
            DifferentialAbundanceDesignIssue(
                code="unsupported_multiple_testing_scope",
                message=(
                    "multiple-testing scope must be one of "
                    "'global_per_analysis', 'per_contrast', or 'hierarchical'"
                ),
                severity="error",
            )
        )
    return DifferentialAbundanceDesignValidationReport(
        valid=not any(issue.severity == "error" for issue in issues),
        condition_replicates=condition_replicates,
        issues=tuple(issues),
    )


def build_multiple_testing_scope_benchmark_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    condition_a: str,
    condition_b: str,
    scopes: tuple[str, ...] = (
        "global_per_analysis",
        "per_contrast",
        "hierarchical",
    ),
) -> MultipleTestingScopeBenchmarkReport:
    """Benchmark which multiple-testing scopes are actually supported today."""
    entries: list[MultipleTestingScopeBenchmarkEntry] = []
    da_report = build_differential_abundance_report(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    bh_report = apply_benjamini_hochberg(da_report)
    adjusted_values = [
        entry.adjusted_p_value
        for entry in bh_report.entries
        if entry.adjusted_p_value is not None
    ]
    monotonic = all(
        left <= right
        for left, right in zip(adjusted_values, adjusted_values[1:], strict=False)
    )
    for scope in scopes:
        validation = validate_differential_abundance_design_context(
            design_entries,
            contrasts=((condition_a, condition_b),),
            multiple_testing_scope=scope,
        )
        if scope == "hierarchical":
            entries.append(
                MultipleTestingScopeBenchmarkEntry(
                    scope=scope,
                    status=MultipleTestingScopeBenchmarkStatus.REFUSED,
                    adjusted_p_values_complete=False,
                    adjusted_p_values_monotonic=False,
                    evidence_count=len(bh_report.entries),
                    note="hierarchical multiple-testing support is still refused because no hierarchical correction engine is implemented",
                )
            )
            continue
        entries.append(
            MultipleTestingScopeBenchmarkEntry(
                scope=scope,
                status=(
                    MultipleTestingScopeBenchmarkStatus.SUPPORTED
                    if validation.valid
                    else MultipleTestingScopeBenchmarkStatus.REFUSED
                ),
                adjusted_p_values_complete=all(
                    entry.adjusted_p_value is not None for entry in bh_report.entries
                ),
                adjusted_p_values_monotonic=monotonic,
                evidence_count=len(bh_report.entries),
                note=(
                    "benjamini-hochberg-corrected report remains complete and monotonic under the current one-contrast benchmark surface"
                    if validation.valid
                    else "design validation failed before a supported multiple-testing benchmark could be claimed"
                ),
            )
        )
    note = "multiple-testing benchmark distinguishes supported report-wide correction from explicitly refused hierarchical scope"
    return MultipleTestingScopeBenchmarkReport(entries=tuple(entries), note=note)


__all__ = [
    "build_multiple_testing_scope_benchmark_report",
    "validate_differential_abundance_design_context",
]
