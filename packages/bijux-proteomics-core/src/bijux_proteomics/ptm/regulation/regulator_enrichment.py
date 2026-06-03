# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned kinase and phosphatase enrichment over regulated PTM sites."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import math
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.ptm.parsing.site_annotation_import import (
    PtmSiteAnnotationMappingReport,
)
from bijux_proteomics.ptm.quant.differential_analysis import (
    PtmSiteDifferentialEntry,
    PtmSiteDifferentialReport,
)
from bijux_proteomics_foundation import JsonModel


class PtmRegulatorDirection(StrEnum):
    """Direction of the regulated phosphosite set supporting a regulator."""

    UPREGULATED = "upregulated"
    DOWNREGULATED = "downregulated"


class PtmRegulatorKind(StrEnum):
    """Substrate-annotation regulator kind preserved in PTM enrichment."""

    KINASE = "kinase"
    PHOSPHATASE = "phosphatase"


class PtmRegulatorEnrichmentPolicy(JsonModel):
    """Foreground-selection and evidence-quality policy for PTM regulator enrichment."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    include_ambiguous_sites: bool = False
    include_low_localization_sites: bool = False


class PtmRegulatorEnrichmentEntry(JsonModel):
    """One regulator enrichment result with explicit supporting-site evidence."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(..., min_length=1)
    regulator_kind: PtmRegulatorKind
    direction: PtmRegulatorDirection
    supporting_site_count: int = Field(..., ge=1)
    supporting_sites: tuple[str, ...] = Field(default_factory=tuple)
    regulated_site_count: int = Field(..., ge=0)
    annotated_regulated_site_count: int = Field(..., ge=0)
    background_annotated_site_count: int = Field(..., ge=0)
    regulator_background_site_count: int = Field(..., ge=0)
    expected_supporting_site_count: float = Field(..., ge=0.0)
    annotation_coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)


class PtmRegulatorEnrichmentSummary(JsonModel):
    """Stable summary over one PTM regulator enrichment pass."""

    model_config = ConfigDict(extra="forbid")

    eligible_site_count: int = Field(..., ge=0)
    upregulated_site_count: int = Field(..., ge=0)
    downregulated_site_count: int = Field(..., ge=0)
    annotated_upregulated_site_count: int = Field(..., ge=0)
    annotated_downregulated_site_count: int = Field(..., ge=0)
    evaluated_regulator_count: int = Field(..., ge=0)
    kinase_result_count: int = Field(..., ge=0)
    phosphatase_result_count: int = Field(..., ge=0)
    enriched_regulator_count: int = Field(..., ge=0)


class PtmRegulatorEnrichmentReport(JsonModel):
    """Stable kinase/phosphatase enrichment report over one PTM contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    policy: PtmRegulatorEnrichmentPolicy
    entries: tuple[PtmRegulatorEnrichmentEntry, ...] = Field(default_factory=tuple)
    summary: PtmRegulatorEnrichmentSummary
    note: str = Field(..., min_length=1)


def build_ptm_regulator_enrichment_report(
    differential_report: PtmSiteDifferentialReport,
    annotation_mapping_report: PtmSiteAnnotationMappingReport,
    *,
    policy: PtmRegulatorEnrichmentPolicy | None = None,
) -> PtmRegulatorEnrichmentReport:
    """Score kinase and phosphatase substrate annotations over regulated PTM sites."""

    active_policy = policy or PtmRegulatorEnrichmentPolicy()
    eligible_entries = tuple(
        entry
        for entry in differential_report.entries
        if _site_passes_evidence_policy(entry, policy=active_policy)
    )
    eligible_site_keys = {entry.site_key for entry in eligible_entries}
    annotations_by_site = _group_regulator_annotations(
        annotation_mapping_report=annotation_mapping_report,
        eligible_site_keys=eligible_site_keys,
    )
    upregulated_sites = _regulated_site_keys(
        eligible_entries,
        direction=PtmRegulatorDirection.UPREGULATED,
        policy=active_policy,
    )
    downregulated_sites = _regulated_site_keys(
        eligible_entries,
        direction=PtmRegulatorDirection.DOWNREGULATED,
        policy=active_policy,
    )

    entries = _evaluate_regulator_entries(
        differential_report=differential_report,
        annotations_by_site=annotations_by_site,
        upregulated_sites=upregulated_sites,
        downregulated_sites=downregulated_sites,
    )
    adjusted_entries = _apply_benjamini_hochberg(entries)

    return PtmRegulatorEnrichmentReport(
        condition_a=differential_report.condition_a,
        condition_b=differential_report.condition_b,
        policy=active_policy,
        entries=tuple(
            sorted(
                adjusted_entries,
                key=lambda entry: (
                    1.0 if entry.adjusted_p_value is None else entry.adjusted_p_value,
                    entry.p_value,
                    entry.direction.value,
                    entry.regulator_kind.value,
                    entry.regulator,
                ),
            )
        ),
        summary=PtmRegulatorEnrichmentSummary(
            eligible_site_count=len(eligible_site_keys),
            upregulated_site_count=len(upregulated_sites),
            downregulated_site_count=len(downregulated_sites),
            annotated_upregulated_site_count=len(
                _annotated_site_keys(
                    annotations_by_site=annotations_by_site,
                    site_keys=upregulated_sites,
                )
            ),
            annotated_downregulated_site_count=len(
                _annotated_site_keys(
                    annotations_by_site=annotations_by_site,
                    site_keys=downregulated_sites,
                )
            ),
            evaluated_regulator_count=len(adjusted_entries),
            kinase_result_count=sum(
                1
                for entry in adjusted_entries
                if entry.regulator_kind is PtmRegulatorKind.KINASE
            ),
            phosphatase_result_count=sum(
                1
                for entry in adjusted_entries
                if entry.regulator_kind is PtmRegulatorKind.PHOSPHATASE
            ),
            enriched_regulator_count=sum(
                1
                for entry in adjusted_entries
                if entry.adjusted_p_value is not None
                and entry.adjusted_p_value <= active_policy.max_adjusted_p_value
            ),
        ),
        note=(
            "ptm regulator enrichment preserves kinase and phosphatase substrate annotations over one regulated-site contrast, keeps exact supporting-site ledgers, and applies benjamini-hochberg correction across evaluated regulator-direction results"
        ),
    )


def render_ptm_regulator_enrichment_summary_tsv(
    report: PtmRegulatorEnrichmentReport,
) -> str:
    """Render one compact PTM regulator enrichment summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition_a",
            "condition_b",
            "eligible_site_count",
            "upregulated_site_count",
            "downregulated_site_count",
            "annotated_upregulated_site_count",
            "annotated_downregulated_site_count",
            "evaluated_regulator_count",
            "kinase_result_count",
            "phosphatase_result_count",
            "enriched_regulator_count",
        )
    )
    writer.writerow(
        (
            report.condition_a,
            report.condition_b,
            report.summary.eligible_site_count,
            report.summary.upregulated_site_count,
            report.summary.downregulated_site_count,
            report.summary.annotated_upregulated_site_count,
            report.summary.annotated_downregulated_site_count,
            report.summary.evaluated_regulator_count,
            report.summary.kinase_result_count,
            report.summary.phosphatase_result_count,
            report.summary.enriched_regulator_count,
        )
    )
    return buffer.getvalue()


def render_ptm_regulator_enrichment_tsv(
    report: PtmRegulatorEnrichmentReport,
) -> str:
    """Render PTM regulator enrichment rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "regulator",
            "regulator_kind",
            "direction",
            "supporting_site_count",
            "supporting_sites",
            "regulated_site_count",
            "annotated_regulated_site_count",
            "background_annotated_site_count",
            "regulator_background_site_count",
            "expected_supporting_site_count",
            "annotation_coverage_fraction",
            "enrichment_ratio",
            "p_value",
            "adjusted_p_value",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.regulator,
                entry.regulator_kind.value,
                entry.direction.value,
                entry.supporting_site_count,
                ";".join(entry.supporting_sites),
                entry.regulated_site_count,
                entry.annotated_regulated_site_count,
                entry.background_annotated_site_count,
                entry.regulator_background_site_count,
                f"{entry.expected_supporting_site_count:g}",
                f"{entry.annotation_coverage_fraction:g}",
                "" if entry.enrichment_ratio is None else f"{entry.enrichment_ratio:g}",
                f"{entry.p_value:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
            )
        )
    return buffer.getvalue()


def export_ptm_regulator_enrichment_summary_tsv(
    report: PtmRegulatorEnrichmentReport,
    path: Path,
) -> None:
    """Write PTM regulator enrichment summary to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_regulator_enrichment_summary_tsv(report))


def export_ptm_regulator_enrichment_tsv(
    report: PtmRegulatorEnrichmentReport,
    path: Path,
) -> None:
    """Write PTM regulator enrichment rows to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_regulator_enrichment_tsv(report))


def _evaluate_regulator_entries(
    *,
    differential_report: PtmSiteDifferentialReport,
    annotations_by_site: dict[str, dict[PtmRegulatorKind, tuple[str, ...]]],
    upregulated_sites: set[str],
    downregulated_sites: set[str],
) -> tuple[PtmRegulatorEnrichmentEntry, ...]:
    entries_by_direction = {
        PtmRegulatorDirection.UPREGULATED: upregulated_sites,
        PtmRegulatorDirection.DOWNREGULATED: downregulated_sites,
    }
    results: list[PtmRegulatorEnrichmentEntry] = []
    for direction, foreground_sites in entries_by_direction.items():
        if not foreground_sites:
            continue
        for regulator_kind in (PtmRegulatorKind.KINASE, PtmRegulatorKind.PHOSPHATASE):
            background_sites = {
                site_key
                for site_key, regulator_sets in annotations_by_site.items()
                if regulator_sets[regulator_kind]
            }
            annotated_foreground = {
                site_key
                for site_key in foreground_sites
                if annotations_by_site.get(site_key, {}).get(regulator_kind, ())
            }
            if not background_sites or not annotated_foreground:
                continue
            regulator_to_sites = _regulator_site_index(
                annotations_by_site=annotations_by_site,
                regulator_kind=regulator_kind,
            )
            for regulator, regulator_background_sites in regulator_to_sites.items():
                supporting_sites = tuple(
                    sorted(annotated_foreground & regulator_background_sites)
                )
                if not supporting_sites:
                    continue
                expected_supporting_site_count = (
                    len(annotated_foreground)
                    * len(regulator_background_sites)
                    / len(background_sites)
                )
                enrichment_ratio = (
                    len(supporting_sites) / expected_supporting_site_count
                    if expected_supporting_site_count > 0.0
                    else None
                )
                results.append(
                    PtmRegulatorEnrichmentEntry(
                        regulator=regulator,
                        regulator_kind=regulator_kind,
                        direction=direction,
                        supporting_site_count=len(supporting_sites),
                        supporting_sites=supporting_sites,
                        regulated_site_count=len(foreground_sites),
                        annotated_regulated_site_count=len(annotated_foreground),
                        background_annotated_site_count=len(background_sites),
                        regulator_background_site_count=len(regulator_background_sites),
                        expected_supporting_site_count=round(
                            expected_supporting_site_count,
                            6,
                        ),
                        annotation_coverage_fraction=round(
                            len(supporting_sites) / len(foreground_sites),
                            6,
                        ),
                        enrichment_ratio=(
                            None
                            if enrichment_ratio is None
                            else round(enrichment_ratio, 6)
                        ),
                        p_value=_hypergeometric_upper_tail(
                            overlap_count=len(supporting_sites),
                            term_background_count=len(regulator_background_sites),
                            foreground_size=len(annotated_foreground),
                            background_size=len(background_sites),
                        ),
                    )
                )
    return tuple(results)


def _annotated_site_keys(
    *,
    annotations_by_site: dict[str, dict[PtmRegulatorKind, tuple[str, ...]]],
    site_keys: set[str],
) -> set[str]:
    return {
        site_key
        for site_key in site_keys
        if any(annotations_by_site.get(site_key, {}).values())
    }


def _regulated_site_keys(
    differential_entries: tuple[PtmSiteDifferentialEntry, ...],
    *,
    direction: PtmRegulatorDirection,
    policy: PtmRegulatorEnrichmentPolicy,
) -> set[str]:
    regulated: set[str] = set()
    for entry in differential_entries:
        adjusted_p_value = entry.adjusted_p_value
        if adjusted_p_value is None:
            adjusted_p_value = entry.p_value
        if adjusted_p_value > policy.max_adjusted_p_value:
            continue
        effective_log2_fold_change = _effective_log2_fold_change(entry)
        if abs(effective_log2_fold_change) < policy.min_absolute_log2_fold_change:
            continue
        if (
            direction is PtmRegulatorDirection.UPREGULATED
            and effective_log2_fold_change > 0.0
        ) or (
            direction is PtmRegulatorDirection.DOWNREGULATED
            and effective_log2_fold_change < 0.0
        ):
            regulated.add(entry.site_key)
    return regulated


def _group_regulator_annotations(
    *,
    annotation_mapping_report: PtmSiteAnnotationMappingReport,
    eligible_site_keys: set[str],
) -> dict[str, dict[PtmRegulatorKind, tuple[str, ...]]]:
    grouped: dict[str, dict[PtmRegulatorKind, set[str]]] = {}
    for entry in annotation_mapping_report.matched_annotations:
        if entry.site_key not in eligible_site_keys:
            continue
        site_entry = grouped.setdefault(
            entry.site_key,
            {
                PtmRegulatorKind.KINASE: set(),
                PtmRegulatorKind.PHOSPHATASE: set(),
            },
        )
        site_entry[PtmRegulatorKind.KINASE].update(entry.kinases)
        site_entry[PtmRegulatorKind.PHOSPHATASE].update(entry.phosphatases)
    return {
        site_key: {
            regulator_kind: tuple(sorted(regulators))
            for regulator_kind, regulators in regulator_sets.items()
        }
        for site_key, regulator_sets in grouped.items()
    }


def _regulator_site_index(
    *,
    annotations_by_site: dict[str, dict[PtmRegulatorKind, tuple[str, ...]]],
    regulator_kind: PtmRegulatorKind,
) -> dict[str, set[str]]:
    regulator_to_sites: dict[str, set[str]] = {}
    for site_key, regulator_sets in annotations_by_site.items():
        for regulator in regulator_sets[regulator_kind]:
            regulator_to_sites.setdefault(regulator, set()).add(site_key)
    return regulator_to_sites


def _apply_benjamini_hochberg(
    entries: tuple[PtmRegulatorEnrichmentEntry, ...],
) -> tuple[PtmRegulatorEnrichmentEntry, ...]:
    if not entries:
        return ()
    total = len(entries)
    ranked_indices = sorted(
        range(total),
        key=lambda index: (
            entries[index].p_value,
            entries[index].direction.value,
            entries[index].regulator_kind.value,
            entries[index].regulator,
        ),
    )
    adjusted = [1.0] * total
    running_minimum = 1.0
    for reverse_rank, index in enumerate(reversed(ranked_indices), start=1):
        rank = total - reverse_rank + 1
        candidate = entries[index].p_value * total / rank
        running_minimum = min(running_minimum, candidate)
        adjusted[index] = min(1.0, running_minimum)
    return tuple(
        entry.model_copy(update={"adjusted_p_value": round(adjusted[index], 12)})
        for index, entry in enumerate(entries)
    )


def _effective_log2_fold_change(entry: PtmSiteDifferentialEntry) -> float:
    if entry.corrected_log2_fold_change is not None:
        return entry.corrected_log2_fold_change
    return entry.log2_fold_change


def _hypergeometric_upper_tail(
    *,
    overlap_count: int,
    term_background_count: int,
    foreground_size: int,
    background_size: int,
) -> float:
    maximum_overlap = min(term_background_count, foreground_size)
    denominator = math.comb(background_size, foreground_size)
    probability = 0.0
    for overlap in range(overlap_count, maximum_overlap + 1):
        probability += (
            math.comb(term_background_count, overlap)
            * math.comb(
                background_size - term_background_count,
                foreground_size - overlap,
            )
            / denominator
        )
    return round(min(probability, 1.0), 12)


def _site_passes_evidence_policy(
    entry: PtmSiteDifferentialEntry,
    *,
    policy: PtmRegulatorEnrichmentPolicy,
) -> bool:
    if not policy.include_low_localization_sites and entry.low_localization:
        return False
    return not (
        not policy.include_ambiguous_sites and (entry.ambiguous or entry.shared_peptide)
    )
