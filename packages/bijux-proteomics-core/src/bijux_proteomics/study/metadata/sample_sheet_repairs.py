# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned sample-sheet repair suggestions over parsed study metadata."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from difflib import SequenceMatcher
from io import StringIO
import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignReport,
)
from bijux_proteomics.study.design.experiment_design import (
    ExperimentDesign,
    coerce_experiment_design,
)
from bijux_proteomics_foundation import JsonModel

SampleSheetRepairConfidence = ConfidenceTier


class SampleSheetRepairSuggestion(JsonModel):
    """One exact but advisory metadata repair suggestion."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    confidence: SampleSheetRepairConfidence
    reason: str = Field(..., min_length=1)
    field: str | None = None
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    condition_ids: tuple[str, ...] = Field(default_factory=tuple)
    current_value: str | None = None
    suggested_value: str | None = None
    suggested_fields: dict[str, str] = Field(default_factory=dict)


class SampleSheetRepairSuggestionSummary(JsonModel):
    """Compact summary over advisory sample-sheet repairs."""

    model_config = ConfigDict(extra="forbid")

    suggestion_count: int = Field(..., ge=0)
    high_confidence_count: int = Field(..., ge=0)
    missing_metadata_sample_count: int = Field(..., ge=0)
    metadata_run_mismatch_count: int = Field(..., ge=0)
    singleton_condition_typo_count: int = Field(..., ge=0)
    missing_technical_replicate_id_count: int = Field(..., ge=0)


class SampleSheetRepairSuggestionReport(JsonModel):
    """Owned advisory repair report for one study design table."""

    model_config = ConfigDict(extra="forbid")

    experiment_design: ExperimentDesign
    parse_rejected_row_count: int = Field(..., ge=0)
    observed_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    observed_run_ids: tuple[str, ...] = Field(default_factory=tuple)
    suggestions: tuple[SampleSheetRepairSuggestion, ...] = Field(default_factory=tuple)
    summary: SampleSheetRepairSuggestionSummary
    note: str = Field(..., min_length=1)


def build_sample_sheet_repair_suggestion_report(
    design: ExperimentalDesignReport
    | ExperimentDesign
    | tuple[ExperimentalDesignEntry, ...],
    *,
    observed_sample_ids: tuple[str, ...] = (),
    observed_run_ids: tuple[str, ...] = (),
) -> SampleSheetRepairSuggestionReport:
    """Detect likely metadata mistakes and suggest exact repairs without applying them."""

    accepted_entries, parse_rejected_row_count = _coerce_design_entries(design)
    experiment_design = coerce_experiment_design(accepted_entries)
    observed_samples = _normalized_ids(observed_sample_ids)
    observed_runs = _normalized_ids(observed_run_ids)
    suggestions = [
        *_missing_metadata_sample_suggestions(
            experiment_design,
            observed_sample_ids=observed_samples,
            observed_run_ids=observed_runs,
        ),
        *_metadata_run_mismatch_suggestions(
            experiment_design,
            observed_run_ids=observed_runs,
        ),
        *_singleton_condition_typo_suggestions(experiment_design),
        *_missing_technical_replicate_id_suggestions(experiment_design),
    ]
    ordered = tuple(
        sorted(
            _deduplicate_suggestions(suggestions),
            key=lambda suggestion: (
                suggestion.code,
                suggestion.sample_ids,
                suggestion.run_ids,
                suggestion.condition_ids,
                suggestion.field or "",
            ),
        )
    )
    return SampleSheetRepairSuggestionReport(
        experiment_design=experiment_design,
        parse_rejected_row_count=parse_rejected_row_count,
        observed_sample_ids=observed_samples,
        observed_run_ids=observed_runs,
        suggestions=ordered,
        summary=SampleSheetRepairSuggestionSummary(
            suggestion_count=len(ordered),
            high_confidence_count=sum(
                1
                for suggestion in ordered
                if suggestion.confidence is SampleSheetRepairConfidence.HIGH
            ),
            missing_metadata_sample_count=sum(
                1
                for suggestion in ordered
                if suggestion.code == "missing_metadata_sample"
            ),
            metadata_run_mismatch_count=sum(
                1
                for suggestion in ordered
                if suggestion.code == "metadata_run_mismatch"
            ),
            singleton_condition_typo_count=sum(
                1
                for suggestion in ordered
                if suggestion.code == "singleton_condition_typo"
            ),
            missing_technical_replicate_id_count=sum(
                1
                for suggestion in ordered
                if suggestion.code == "missing_technical_replicate_id"
            ),
        ),
        note=(
            "sample-sheet repair suggestions are advisory only: they propose exact "
            "metadata repairs with confidence and reason, but they never rewrite "
            "the design table automatically"
        ),
    )


def render_sample_sheet_repair_suggestions_tsv(
    report: SampleSheetRepairSuggestionReport,
) -> str:
    """Render one advisory repair ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "code",
            "confidence",
            "reason",
            "field",
            "sample_ids",
            "run_ids",
            "condition_ids",
            "current_value",
            "suggested_value",
            "suggested_fields_json",
        )
    )
    for suggestion in report.suggestions:
        writer.writerow(
            (
                suggestion.code,
                suggestion.confidence.value,
                suggestion.reason,
                suggestion.field or "",
                ";".join(suggestion.sample_ids),
                ";".join(suggestion.run_ids),
                ";".join(suggestion.condition_ids),
                suggestion.current_value or "",
                suggestion.suggested_value or "",
                json.dumps(suggestion.suggested_fields, sort_keys=True),
            )
        )
    return buffer.getvalue()


def export_sample_sheet_repair_suggestions_tsv(
    report: SampleSheetRepairSuggestionReport,
    path: Path,
) -> None:
    """Write one advisory repair ledger to a governed TSV artifact."""

    write_output_table_tsv(path, render_sample_sheet_repair_suggestions_tsv(report))


def _coerce_design_entries(
    design: ExperimentalDesignReport
    | ExperimentDesign
    | tuple[ExperimentalDesignEntry, ...],
) -> tuple[tuple[ExperimentalDesignEntry, ...], int]:
    if isinstance(design, ExperimentalDesignReport):
        return design.accepted_entries, len(design.rejected_rows)
    experiment_design = coerce_experiment_design(design)
    return experiment_design.entries, 0


def _missing_metadata_sample_suggestions(
    experiment_design: ExperimentDesign,
    *,
    observed_sample_ids: tuple[str, ...],
    observed_run_ids: tuple[str, ...],
) -> tuple[SampleSheetRepairSuggestion, ...]:
    if not observed_sample_ids:
        return ()
    metadata_sample_ids = {sample.sample_id for sample in experiment_design.samples}
    unmatched_runs = tuple(
        sorted(set(observed_run_ids) - {run.run_id for run in experiment_design.runs})
    )
    missing_samples = tuple(
        sorted(
            sample_id
            for sample_id in observed_sample_ids
            if sample_id not in metadata_sample_ids
        )
    )
    suggestions: list[SampleSheetRepairSuggestion] = []
    for sample_id in missing_samples:
        suggested_fields = {"sample_id": sample_id}
        matched_run, run_similarity = _best_matching_run(
            sample_id,
            unmatched_runs,
        )
        confidence = SampleSheetRepairConfidence.MEDIUM
        reason = (
            "observed sample id is present in analysis data but absent from metadata"
        )
        if matched_run is not None:
            suggested_fields["spectra_file"] = matched_run
            confidence = (
                SampleSheetRepairConfidence.HIGH
                if run_similarity >= 0.9
                else SampleSheetRepairConfidence.MEDIUM
            )
            reason += (
                "; the suggested run id matches the missing sample id more closely "
                "than the metadata runs"
            )
        elif len(missing_samples) == 1 and len(unmatched_runs) == 1:
            suggested_fields["spectra_file"] = unmatched_runs[0]
            confidence = SampleSheetRepairConfidence.MEDIUM
            reason += "; one unmatched observed run remains, so it is the only plausible run assignment"
        else:
            confidence = SampleSheetRepairConfidence.LOW
            reason += "; run assignment still needs manual confirmation"
        suggested_run_ids = (
            ()
            if "spectra_file" not in suggested_fields
            else (suggested_fields["spectra_file"],)
        )
        suggestions.append(
            SampleSheetRepairSuggestion(
                code="missing_metadata_sample",
                confidence=confidence,
                reason=reason,
                field="sample_id",
                sample_ids=(sample_id,),
                run_ids=suggested_run_ids,
                suggested_value=sample_id,
                suggested_fields=suggested_fields,
            )
        )
    return tuple(suggestions)


def _metadata_run_mismatch_suggestions(
    experiment_design: ExperimentDesign,
    *,
    observed_run_ids: tuple[str, ...],
) -> tuple[SampleSheetRepairSuggestion, ...]:
    if not observed_run_ids:
        return ()
    observed_run_set = set(observed_run_ids)
    unmatched_observed_runs = tuple(
        sorted(observed_run_set - {run.run_id for run in experiment_design.runs})
    )
    suggestions: list[SampleSheetRepairSuggestion] = []
    for run in experiment_design.runs:
        if run.run_id in observed_run_set:
            continue
        candidate_run, similarity = _best_matching_run(
            run.sample_id,
            unmatched_observed_runs,
            current_run_id=run.run_id,
        )
        if candidate_run is not None and similarity >= 0.75:
            suggestions.append(
                SampleSheetRepairSuggestion(
                    code="metadata_run_mismatch",
                    confidence=(
                        SampleSheetRepairConfidence.HIGH
                        if similarity >= 0.9
                        else SampleSheetRepairConfidence.MEDIUM
                    ),
                    reason=(
                        "metadata row references a run that is absent from observed "
                        "data, and one unmatched observed run is the closest name match"
                    ),
                    field="spectra_file",
                    sample_ids=(run.sample_id,),
                    run_ids=(run.run_id, candidate_run),
                    current_value=run.run_id,
                    suggested_value=candidate_run,
                    suggested_fields={"spectra_file": candidate_run},
                )
            )
            continue
        suggestions.append(
            SampleSheetRepairSuggestion(
                code="metadata_run_mismatch",
                confidence=SampleSheetRepairConfidence.MEDIUM,
                reason=(
                    "metadata row references a run that is absent from observed "
                    "data and no better run-name candidate is available"
                ),
                field="spectra_file",
                sample_ids=(run.sample_id,),
                run_ids=(run.run_id,),
                current_value=run.run_id,
                suggested_fields={},
            )
        )
    return tuple(suggestions)


def _singleton_condition_typo_suggestions(
    experiment_design: ExperimentDesign,
) -> tuple[SampleSheetRepairSuggestion, ...]:
    counts = Counter(sample.condition for sample in experiment_design.samples)
    conditions = tuple(sorted(counts))
    suggestions: list[SampleSheetRepairSuggestion] = []
    for condition, count in sorted(counts.items()):
        if count != 1:
            continue
        best_match = None
        best_similarity = 0.0
        for candidate in conditions:
            if candidate == condition or counts[candidate] < 2:
                continue
            similarity = _string_similarity(condition, candidate)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate
        if best_match is None or best_similarity < 0.75:
            continue
        sample_ids = tuple(
            sorted(
                sample.sample_id
                for sample in experiment_design.samples
                if sample.condition == condition
            )
        )
        suggestions.append(
            SampleSheetRepairSuggestion(
                code="singleton_condition_typo",
                confidence=(
                    SampleSheetRepairConfidence.HIGH
                    if best_similarity >= 0.9
                    else SampleSheetRepairConfidence.MEDIUM
                ),
                reason=(
                    "condition label creates a singleton group while one larger "
                    "condition label is a near string match"
                ),
                field="condition",
                sample_ids=sample_ids,
                condition_ids=(condition, best_match),
                current_value=condition,
                suggested_value=best_match,
                suggested_fields={"condition": best_match},
            )
        )
    return tuple(suggestions)


def _missing_technical_replicate_id_suggestions(
    experiment_design: ExperimentDesign,
) -> tuple[SampleSheetRepairSuggestion, ...]:
    entries_by_sample_condition: dict[
        tuple[str, str], list[ExperimentalDesignEntry]
    ] = defaultdict(list)
    for entry in experiment_design.entries:
        entries_by_sample_condition[(entry.sample_id, entry.condition)].append(entry)
    suggestions: list[SampleSheetRepairSuggestion] = []
    for (sample_id, condition), entries in sorted(entries_by_sample_condition.items()):
        if len(entries) <= 1:
            continue
        if all(entry.technical_replicate_id not in (None, "") for entry in entries):
            continue
        for entry in sorted(entries, key=lambda record: record.spectra_file):
            if entry.technical_replicate_id not in (None, ""):
                continue
            suggested_value = Path(entry.spectra_file).stem
            suggestions.append(
                SampleSheetRepairSuggestion(
                    code="missing_technical_replicate_id",
                    confidence=SampleSheetRepairConfidence.HIGH,
                    reason=(
                        "multiple rows share one biological sample and condition but "
                        "this run is missing a technical replicate identifier"
                    ),
                    field="technical_replicate_id",
                    sample_ids=(sample_id,),
                    run_ids=(entry.spectra_file,),
                    condition_ids=(condition,),
                    suggested_value=suggested_value,
                    suggested_fields={"technical_replicate_id": suggested_value},
                )
            )
    return tuple(suggestions)


def _best_matching_run(
    sample_id: str,
    candidate_runs: tuple[str, ...],
    *,
    current_run_id: str | None = None,
) -> tuple[str | None, float]:
    best_run = None
    best_similarity = 0.0
    sample_token = Path(sample_id).stem.lower()
    current_token = (
        None if current_run_id is None else Path(current_run_id).stem.lower()
    )
    for run_id in candidate_runs:
        run_token = Path(run_id).stem.lower()
        similarity = max(
            _string_similarity(sample_token, run_token),
            0.0
            if current_token is None
            else _string_similarity(current_token, run_token),
        )
        if similarity > best_similarity:
            best_run = run_id
            best_similarity = similarity
    return best_run, best_similarity


def _string_similarity(left: str, right: str) -> float:
    return SequenceMatcher(a=left.lower(), b=right.lower()).ratio()


def _normalized_ids(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({value.strip() for value in values if value.strip()}))


def _deduplicate_suggestions(
    suggestions: list[SampleSheetRepairSuggestion],
) -> tuple[SampleSheetRepairSuggestion, ...]:
    deduped: dict[tuple[object, ...], SampleSheetRepairSuggestion] = {}
    for suggestion in suggestions:
        key = (
            suggestion.code,
            suggestion.field,
            suggestion.sample_ids,
            suggestion.run_ids,
            suggestion.condition_ids,
            suggestion.current_value,
            suggestion.suggested_value,
            tuple(sorted(suggestion.suggested_fields.items())),
        )
        deduped[key] = suggestion
    return tuple(deduped.values())


__all__ = [
    "SampleSheetRepairConfidence",
    "SampleSheetRepairSuggestion",
    "SampleSheetRepairSuggestionReport",
    "SampleSheetRepairSuggestionSummary",
    "build_sample_sheet_repair_suggestion_report",
    "export_sample_sheet_repair_suggestions_tsv",
    "render_sample_sheet_repair_suggestions_tsv",
]
