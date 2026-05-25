# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Descriptor-driven real-data subset builder over shipped public benchmark datasets."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.public_benchmark_descriptors import (
    PublicBenchmarkApproximateCount,
    PublicBenchmarkContrast,
    PublicBenchmarkDescriptor,
    PublicBenchmarkExpectedSignalSubjectKind,
    PublicBenchmarkSampleGroup,
    PublicBenchmarkSampleMetadata,
)
from bijux_proteomics_foundation import JsonModel


class PublicBenchmarkSubsetInput(JsonModel):
    """One subsetted benchmark input carried as content plus stable metadata."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1)
    schema_id: str = Field(..., min_length=1)
    original_repo_relative_path: str = Field(..., min_length=1)
    subset_relative_path: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    row_count: int | None = Field(default=None, ge=0)
    note: str = Field(..., min_length=1)


class PublicBenchmarkSubsetCountRange(JsonModel):
    """One conservative expected-count range for a subsetted benchmark rerun."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str = Field(..., min_length=1)
    min_expected: int = Field(..., ge=0)
    max_expected: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class PublicBenchmarkSubsetReport(JsonModel):
    """Subset package over one shipped public benchmark descriptor."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    source_dataset_id: str = Field(..., min_length=1)
    selected_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    selected_entity_anchors: tuple[str, ...] = Field(default_factory=tuple)
    preserved_signal_ids: tuple[str, ...] = Field(default_factory=tuple)
    preserved_decoy_entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    preserved_contaminant_entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_groups: tuple[PublicBenchmarkSampleGroup, ...] = Field(default_factory=tuple)
    sample_metadata: tuple[PublicBenchmarkSampleMetadata, ...] = Field(default_factory=tuple)
    contrast: PublicBenchmarkContrast
    subset_inputs: tuple[PublicBenchmarkSubsetInput, ...] = Field(default_factory=tuple)
    expected_count_ranges: tuple[PublicBenchmarkSubsetCountRange, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class _SignalAnchor(JsonModel):
    """Internal signal anchor used while selecting subset entities."""

    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(..., min_length=1)
    subject_kind: PublicBenchmarkExpectedSignalSubjectKind
    protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    residue: str | None = None
    position: int | None = Field(default=None, ge=1)
    modification_name: str | None = None


class _TabularSubsetResult(JsonModel):
    """Internal filtered tabular content with row-level preservation details."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., min_length=1)
    row_count: int = Field(..., ge=0)
    preserved_decoy_ids: tuple[str, ...] = Field(default_factory=tuple)
    preserved_contaminant_ids: tuple[str, ...] = Field(default_factory=tuple)
    preserved_signal_ids: tuple[str, ...] = Field(default_factory=tuple)


def build_public_benchmark_subset(
    dataset_descriptor: PublicBenchmarkDescriptor,
    max_samples: int,
    max_entities: int,
) -> PublicBenchmarkSubsetReport:
    """Build a smaller real-data subset from one shipped public benchmark descriptor."""

    if max_samples < 1:
        raise ValueError("public benchmark subset requires max_samples >= 1")
    if max_entities < 1:
        raise ValueError("public benchmark subset requires max_entities >= 1")

    selected_metadata = _select_sample_metadata(dataset_descriptor, max_samples=max_samples)
    selected_sample_ids = tuple(sample.sample_id for sample in selected_metadata)
    signal_anchors = _signal_anchors(dataset_descriptor)
    detected_anchor_state = _detect_required_entity_anchors(dataset_descriptor)
    required_entity_ids = tuple(
        dict.fromkeys(
            (
                *(anchor.site_key or anchor.protein_ref for anchor in signal_anchors[:1]),
                *detected_anchor_state["decoy_entity_ids"][:1],
                *detected_anchor_state["contaminant_entity_ids"][:1],
            )
        )
    )
    if len(required_entity_ids) > max_entities:
        raise ValueError(
            "public benchmark subset max_entities is too small to preserve one known "
            "signal together with mandatory decoy and contaminant integrity anchors"
        )
    selected_entity_ids = _select_entity_ids(
        selected_sample_ids=selected_sample_ids,
        max_entities=max_entities,
        required_entity_ids=required_entity_ids,
        biological_entity_ids=detected_anchor_state["biological_entity_ids"],
        sample_coverage=detected_anchor_state["sample_coverage"],
    )
    if signal_anchors and not any(
        (anchor.site_key or anchor.protein_ref) in set(selected_entity_ids)
        for anchor in signal_anchors
    ):
        raise ValueError(
            "public benchmark subset could not preserve any declared biological signal "
            "under the requested entity budget"
        )

    subset_inputs: list[PublicBenchmarkSubsetInput] = []
    preserved_signal_ids: set[str] = set()
    preserved_decoy_ids: set[str] = set()
    preserved_contaminant_ids: set[str] = set()
    repo_root = _repo_root()
    for source in dataset_descriptor.source_files:
        source_path = repo_root / source.repo_relative_path
        subset_relative_path = f"subset_inputs/{source.source_id}/{source_path.name}"
        if source.schema_id in _TABULAR_SCHEMA_IDS:
            subset = _build_tabular_subset(
                source_path=source_path,
                schema_id=source.schema_id,
                selected_sample_ids=selected_sample_ids,
                selected_entity_ids=selected_entity_ids,
                signal_anchors=signal_anchors,
            )
            subset_inputs.append(
                PublicBenchmarkSubsetInput(
                    source_id=source.source_id,
                    schema_id=source.schema_id,
                    original_repo_relative_path=source.repo_relative_path,
                    subset_relative_path=subset_relative_path,
                    content=subset.content,
                    row_count=subset.row_count,
                    note=(
                        "subset content preserves selected conditions, replicate rows, "
                        "entity anchors, and explicit decoy or contaminant rows when present"
                    ),
                )
            )
            preserved_signal_ids.update(subset.preserved_signal_ids)
            preserved_decoy_ids.update(subset.preserved_decoy_ids)
            preserved_contaminant_ids.update(subset.preserved_contaminant_ids)
            continue
        if source.schema_id == "proteins_fasta":
            fasta_content = _subset_fasta(
                source_path=source_path,
                selected_entity_ids=selected_entity_ids,
                signal_anchors=signal_anchors,
            )
            subset_inputs.append(
                PublicBenchmarkSubsetInput(
                    source_id=source.source_id,
                    schema_id=source.schema_id,
                    original_repo_relative_path=source.repo_relative_path,
                    subset_relative_path=subset_relative_path,
                    content=fasta_content,
                    row_count=sum(1 for line in fasta_content.splitlines() if line.startswith(">")),
                    note=(
                        "subset FASTA preserves selected signal proteins together with "
                        "chosen decoy or contaminant accessions when they are present"
                    ),
                )
            )
            continue
        text_content = source_path.read_text(encoding="utf-8")
        subset_inputs.append(
            PublicBenchmarkSubsetInput(
                source_id=source.source_id,
                schema_id=source.schema_id,
                original_repo_relative_path=source.repo_relative_path,
                subset_relative_path=subset_relative_path,
                content=text_content,
                row_count=None,
                note=(
                    "non-tabular support input is preserved verbatim because it does not "
                    "carry sample- or entity-level benchmark rows"
                ),
            )
        )

    if dataset_descriptor.expected_biological_signals and not preserved_signal_ids:
        raise ValueError(
            "public benchmark subset did not preserve any declared biological signal rows"
        )
    if detected_anchor_state["decoy_entity_ids"] and not preserved_decoy_ids:
        raise ValueError("public benchmark subset did not preserve any declared decoy rows")
    if detected_anchor_state["contaminant_entity_ids"] and not preserved_contaminant_ids:
        raise ValueError(
            "public benchmark subset did not preserve any declared contaminant rows"
        )

    return PublicBenchmarkSubsetReport(
        dataset_id=f"{dataset_descriptor.dataset_id}_subset",
        source_dataset_id=dataset_descriptor.dataset_id,
        selected_sample_ids=selected_sample_ids,
        selected_entity_anchors=selected_entity_ids,
        preserved_signal_ids=tuple(sorted(preserved_signal_ids)),
        preserved_decoy_entity_ids=tuple(sorted(preserved_decoy_ids)),
        preserved_contaminant_entity_ids=tuple(sorted(preserved_contaminant_ids)),
        sample_groups=_subset_sample_groups(dataset_descriptor, selected_sample_ids),
        sample_metadata=selected_metadata,
        contrast=dataset_descriptor.contrast,
        subset_inputs=tuple(subset_inputs),
        expected_count_ranges=_build_count_ranges(
            expected_counts=dataset_descriptor.expected_approximate_counts,
            selected_sample_count=len(selected_sample_ids),
            selected_entity_count=len(selected_entity_ids),
            preserved_signal_count=len(preserved_signal_ids),
            preserved_decoy_count=len(preserved_decoy_ids),
            preserved_contaminant_count=len(preserved_contaminant_ids),
            subset_inputs=tuple(subset_inputs),
        ),
        note=(
            "descriptor-driven subset keeps a balanced condition-aware sample slice, "
            "preserves one declared biological signal when available, and retains "
            "explicit decoy or contaminant integrity rows from the shipped real-data assets"
        ),
    )


_TABULAR_SCHEMA_IDS = {
    "annotation_tsv",
    "design_tsv",
    "evidence_tsv",
    "evidence_txt",
    "feature_tsv",
    "input_tsv",
    "peptides_txt",
    "protein_groups_txt",
    "result_tsv",
}


def _select_sample_metadata(
    descriptor: PublicBenchmarkDescriptor,
    *,
    max_samples: int,
) -> tuple[PublicBenchmarkSampleMetadata, ...]:
    groups = tuple(descriptor.sample_groups)
    if max_samples < len(groups):
        raise ValueError(
            "public benchmark subset max_samples must preserve at least one sample per condition"
        )
    metadata_by_group = {
        group.group_id: [
            sample
            for sample in descriptor.sample_metadata
            if sample.group_id == group.group_id
        ]
        for group in groups
    }
    selected: list[PublicBenchmarkSampleMetadata] = []
    positions = {group.group_id: 0 for group in groups}
    for group in groups:
        candidates = metadata_by_group[group.group_id]
        if not candidates:
            raise ValueError(
                f"public benchmark descriptor group {group.group_id!r} has no sample metadata"
            )
        selected.append(candidates[0])
        positions[group.group_id] = 1
    remaining = max_samples - len(selected)
    while remaining > 0:
        progressed = False
        for group in groups:
            candidates = metadata_by_group[group.group_id]
            position = positions[group.group_id]
            if position >= len(candidates):
                continue
            selected.append(candidates[position])
            positions[group.group_id] = position + 1
            remaining -= 1
            progressed = True
            if remaining == 0:
                break
        if not progressed:
            break
    return tuple(selected)


def _subset_sample_groups(
    descriptor: PublicBenchmarkDescriptor,
    selected_sample_ids: tuple[str, ...],
) -> tuple[PublicBenchmarkSampleGroup, ...]:
    selected = set(selected_sample_ids)
    groups = []
    for group in descriptor.sample_groups:
        group_sample_ids = tuple(sample_id for sample_id in group.sample_ids if sample_id in selected)
        groups.append(
            PublicBenchmarkSampleGroup(
                group_id=group.group_id,
                sample_ids=group_sample_ids,
                note=group.note,
            )
        )
    return tuple(groups)


def _select_entity_ids(
    *,
    selected_sample_ids: tuple[str, ...],
    max_entities: int,
    required_entity_ids: tuple[str, ...],
    biological_entity_ids: tuple[str, ...],
    sample_coverage: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    selected = list(required_entity_ids)
    selected_set = set(selected)
    uncovered_samples = set(selected_sample_ids)
    for entity_id in selected:
        uncovered_samples.difference_update(sample_coverage.get(entity_id, ()))
    candidates = [
        entity_id for entity_id in biological_entity_ids if entity_id not in selected_set
    ]
    while len(selected) < max_entities and candidates:
        best_entity = max(
            candidates,
            key=lambda entity_id: (
                len(uncovered_samples.intersection(sample_coverage.get(entity_id, ()))),
                len(sample_coverage.get(entity_id, ())),
                -biological_entity_ids.index(entity_id),
            ),
        )
        selected.append(best_entity)
        selected_set.add(best_entity)
        uncovered_samples.difference_update(sample_coverage.get(best_entity, ()))
        candidates.remove(best_entity)
    return tuple(selected)


def _signal_anchors(
    descriptor: PublicBenchmarkDescriptor,
) -> tuple[_SignalAnchor, ...]:
    anchors = []
    for signal in descriptor.expected_biological_signals:
        if signal.subject_kind is PublicBenchmarkExpectedSignalSubjectKind.PROTEIN:
            anchors.append(
                _SignalAnchor(
                    signal_id=signal.signal_id,
                    subject_kind=signal.subject_kind,
                    protein_ref=signal.subject_id,
                )
            )
            continue
        if signal.subject_kind is PublicBenchmarkExpectedSignalSubjectKind.PTM_SITE:
            protein_ref, residue_position, modification_name = signal.subject_id.split(":")
            residue = residue_position[:1]
            position = int(residue_position[1:])
            anchors.append(
                _SignalAnchor(
                    signal_id=signal.signal_id,
                    subject_kind=signal.subject_kind,
                    protein_ref=protein_ref,
                    site_key=signal.subject_id,
                    residue=residue,
                    position=position,
                    modification_name=modification_name,
                )
            )
            continue
        raise ValueError(
            f"public benchmark subset does not support signal kind {signal.subject_kind.value!r}"
        )
    return tuple(anchors)


def _detect_required_entity_anchors(
    descriptor: PublicBenchmarkDescriptor,
) -> dict[str, object]:
    repo_root = _repo_root()
    biological_entity_ids: list[str] = []
    decoy_entity_ids: list[str] = []
    contaminant_entity_ids: list[str] = []
    sample_coverage: dict[str, set[str]] = {}
    for source in descriptor.source_files:
        if source.schema_id not in _TABULAR_SCHEMA_IDS:
            continue
        rows = _read_tabular_rows(repo_root / source.repo_relative_path, source.schema_id)
        for row in rows:
            entity_ids = _row_entity_ids(row, schema_id=source.schema_id)
            row_samples = _row_sample_ids(row, schema_id=source.schema_id)
            for entity_id in entity_ids:
                if entity_id:
                    sample_coverage.setdefault(entity_id, set()).update(row_samples)
            if _row_is_decoy(row):
                decoy_entity_ids.extend(entity_ids)
                continue
            if _row_is_contaminant(row):
                contaminant_entity_ids.extend(entity_ids)
                continue
            biological_entity_ids.extend(entity_ids)
    return {
        "biological_entity_ids": tuple(dict.fromkeys(entity_id for entity_id in biological_entity_ids if entity_id)),
        "decoy_entity_ids": tuple(dict.fromkeys(entity_id for entity_id in decoy_entity_ids if entity_id)),
        "contaminant_entity_ids": tuple(
            dict.fromkeys(entity_id for entity_id in contaminant_entity_ids if entity_id)
        ),
        "sample_coverage": {
            entity_id: tuple(sorted(sample_ids))
            for entity_id, sample_ids in sorted(sample_coverage.items())
        },
    }


def _build_tabular_subset(
    *,
    source_path: Path,
    schema_id: str,
    selected_sample_ids: tuple[str, ...],
    selected_entity_ids: tuple[str, ...],
    signal_anchors: tuple[_SignalAnchor, ...],
) -> _TabularSubsetResult:
    rows = _read_tabular_rows(source_path, schema_id)
    if not rows:
        return _TabularSubsetResult(
            content=source_path.read_text(encoding="utf-8"),
            row_count=0,
            preserved_decoy_ids=(),
            preserved_contaminant_ids=(),
            preserved_signal_ids=(),
        )
    filtered_rows = []
    preserved_signal_ids: set[str] = set()
    preserved_decoy_ids: set[str] = set()
    preserved_contaminant_ids: set[str] = set()
    for row in rows:
        if not _row_matches_samples(row, schema_id=schema_id, selected_sample_ids=selected_sample_ids):
            continue
        if not _row_matches_entities(
            row,
            schema_id=schema_id,
            selected_entity_ids=selected_entity_ids,
            signal_anchors=signal_anchors,
        ):
            continue
        filtered_rows.append(row)
        row_entity_ids = _row_entity_ids(row, schema_id=schema_id)
        if _row_is_decoy(row):
            preserved_decoy_ids.update(row_entity_ids)
        if _row_is_contaminant(row):
            preserved_contaminant_ids.update(row_entity_ids)
        preserved_signal_ids.update(
            signal.signal_id
            for signal in signal_anchors
            if _row_matches_signal_anchor(row, schema_id=schema_id, signal_anchor=signal)
        )
    content = _render_tabular_rows(
        rows=filtered_rows,
        fieldnames=_subset_fieldnames(
            fieldnames=tuple(rows[0].keys()),
            schema_id=schema_id,
            selected_sample_ids=selected_sample_ids,
        ),
    )
    return _TabularSubsetResult(
        content=content,
        row_count=len(filtered_rows),
        preserved_decoy_ids=tuple(sorted(preserved_decoy_ids)),
        preserved_contaminant_ids=tuple(sorted(preserved_contaminant_ids)),
        preserved_signal_ids=tuple(sorted(preserved_signal_ids)),
    )


def _subset_fasta(
    *,
    source_path: Path,
    selected_entity_ids: tuple[str, ...],
    signal_anchors: tuple[_SignalAnchor, ...],
) -> str:
    selected_proteins = {
        entity_id.split(":")[0] if ":" in entity_id else entity_id for entity_id in selected_entity_ids
    }
    selected_proteins.update(anchor.protein_ref for anchor in signal_anchors)
    blocks: list[str] = []
    current: list[str] = []
    keep_current = False
    for line in source_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(">"):
            if current and keep_current:
                blocks.append("\n".join(current))
            current = [line]
            accession = _header_accession(line)
            keep_current = accession in selected_proteins
            continue
        current.append(line)
    if current and keep_current:
        blocks.append("\n".join(current))
    if not blocks:
        return source_path.read_text(encoding="utf-8")
    return "\n".join(blocks) + "\n"


def _header_accession(header: str) -> str:
    normalized = header.lstrip(">").strip()
    if "|" not in normalized:
        return normalized.split()[0]
    parts = normalized.split("|")
    return parts[1]


def _build_count_ranges(
    *,
    expected_counts: tuple[PublicBenchmarkApproximateCount, ...],
    selected_sample_count: int,
    selected_entity_count: int,
    preserved_signal_count: int,
    preserved_decoy_count: int,
    preserved_contaminant_count: int,
    subset_inputs: tuple[PublicBenchmarkSubsetInput, ...],
) -> tuple[PublicBenchmarkSubsetCountRange, ...]:
    primary_row_budget = max(
        (
            item.row_count or 0
            for item in subset_inputs
            if item.schema_id in {"evidence_tsv", "evidence_txt", "feature_tsv", "input_tsv", "result_tsv"}
        ),
        default=0,
    )
    ranges = []
    integrity_anchor_count = preserved_decoy_count + preserved_contaminant_count
    for count in expected_counts:
        metric_id = count.metric_id
        if "experiment_count" in metric_id:
            min_expected = selected_sample_count
            max_expected = selected_sample_count
            note = "subset keeps an exact sample or experiment count because sample selection is explicit"
        elif any(token in metric_id for token in ("protein", "site", "card", "group_count")):
            min_expected = min(count.expected, max(1, preserved_signal_count))
            max_expected = min(count.expected, selected_entity_count)
            note = (
                "subset keeps at least one signal-bearing biological entity and caps review-facing "
                "entity counts by the selected entity budget"
            )
        else:
            min_expected = min(count.expected, max(1, preserved_signal_count + integrity_anchor_count))
            max_expected = min(count.expected, max(primary_row_budget, min_expected))
            note = (
                "subset keeps one known signal plus explicit integrity rows and bounds broader counts "
                "by the retained primary-input row budget"
            )
        if max_expected < min_expected:
            max_expected = min_expected
        ranges.append(
            PublicBenchmarkSubsetCountRange(
                metric_id=metric_id,
                min_expected=min_expected,
                max_expected=max_expected,
                note=note,
            )
        )
    return tuple(ranges)


def _row_matches_samples(
    row: dict[str, str],
    *,
    schema_id: str,
    selected_sample_ids: tuple[str, ...],
) -> bool:
    selected = set(selected_sample_ids)
    row_sample_ids = _row_sample_ids(row, schema_id=schema_id)
    if not row_sample_ids:
        return True
    return bool(selected.intersection(row_sample_ids))


def _row_matches_entities(
    row: dict[str, str],
    *,
    schema_id: str,
    selected_entity_ids: tuple[str, ...],
    signal_anchors: tuple[_SignalAnchor, ...],
) -> bool:
    if schema_id == "design_tsv":
        return True
    selected = set(selected_entity_ids)
    row_entities = set(_row_entity_ids(row, schema_id=schema_id))
    if not row_entities and schema_id not in {"annotation_tsv", "protein_groups_txt"}:
        return True
    if row_entities.intersection(selected):
        return True
    return any(
        _row_matches_signal_anchor(row, schema_id=schema_id, signal_anchor=signal)
        for signal in signal_anchors
    )


def _row_matches_signal_anchor(
    row: dict[str, str],
    *,
    schema_id: str,
    signal_anchor: _SignalAnchor,
) -> bool:
    row_entities = set(_row_entity_ids(row, schema_id=schema_id))
    if signal_anchor.subject_kind is PublicBenchmarkExpectedSignalSubjectKind.PROTEIN:
        return signal_anchor.protein_ref in row_entities
    if signal_anchor.subject_kind is PublicBenchmarkExpectedSignalSubjectKind.PTM_SITE:
        if schema_id == "annotation_tsv":
            return (
                row.get("protein_ref") == signal_anchor.protein_ref
                and row.get("residue") == signal_anchor.residue
                and row.get("position") == str(signal_anchor.position)
                and row.get("modification_name") == signal_anchor.modification_name
            )
        return signal_anchor.protein_ref in row_entities
    return False


def _row_sample_ids(row: dict[str, str], *, schema_id: str) -> tuple[str, ...]:
    for field_name in ("sample_id", "Experiment"):
        value = _nonempty(row.get(field_name))
        if value is not None:
            return (value,)
    raw_file = _nonempty(row.get("Raw file"))
    if raw_file is not None:
        suffix = raw_file.removeprefix("raw_")
        return (suffix.split(".")[0],)
    return ()


def _row_entity_ids(row: dict[str, str], *, schema_id: str) -> tuple[str, ...]:
    if schema_id == "annotation_tsv":
        protein_ref = _nonempty(row.get("protein_ref"))
        residue = _nonempty(row.get("residue"))
        position = _nonempty(row.get("position"))
        modification_name = _nonempty(row.get("modification_name"))
        values = []
        if protein_ref is not None:
            values.append(protein_ref)
        if None not in {protein_ref, residue, position, modification_name}:
            values.append(f"{protein_ref}:{residue}{position}:{modification_name}")
        return tuple(values)
    for field_name in (
        "proteins",
        "Proteins",
        "Protein IDs",
        "protein_ids",
        "protein_accessions",
        "protein_group",
        "protein_ids_joined",
        "protein_refs",
    ):
        value = _nonempty(row.get(field_name))
        if value is not None:
            return tuple(_split_entity_values(value))
    return ()


def _split_entity_values(value: str) -> tuple[str, ...]:
    normalized = value.replace(",", ";")
    return tuple(part.strip() for part in normalized.split(";") if part.strip())


def _row_is_decoy(row: dict[str, str]) -> bool:
    explicit_values = (
        row.get("Reverse"),
        row.get("decoy_flag"),
        row.get("decoy_label"),
        row.get("is_decoy"),
        row.get("decoy_state"),
    )
    if any(_nonempty(value) in {"+", "1", "true", "decoy"} for value in explicit_values):
        return True
    return any(
        entity.startswith(("REV__", "DECOY_", "DECOY", "Q9DEC"))
        for field_name in ("Proteins", "proteins", "Protein IDs", "protein_ids", "protein_accessions", "protein_group")
        for entity in _split_entity_values(_nonempty(row.get(field_name)) or "")
    )


def _row_is_contaminant(row: dict[str, str]) -> bool:
    explicit_values = (
        row.get("Potential contaminant"),
        row.get("is_contaminant"),
        row.get("contaminant_flag"),
    )
    if any(_nonempty(value) in {"+", "1", "true"} for value in explicit_values):
        return True
    return any(
        entity.startswith("CON__") or "CONTAM" in entity
        for field_name in ("Proteins", "proteins", "Protein IDs", "protein_ids", "protein_accessions", "protein_group")
        for entity in _split_entity_values(_nonempty(row.get(field_name)) or "")
    )


def _read_tabular_rows(path: Path, schema_id: str) -> tuple[dict[str, str], ...]:
    delimiter = "\t"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError(f"{path.name!r} must include a header row")
        return tuple(
            {
                str(key or "").strip(): str(value or "").strip()
                for key, value in row.items()
            }
            for row in reader
        )


def _subset_fieldnames(
    *,
    fieldnames: tuple[str, ...],
    schema_id: str,
    selected_sample_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if schema_id != "protein_groups_txt":
        return fieldnames
    selected_columns = {f"LFQ intensity {sample_id}" for sample_id in selected_sample_ids}
    static_fields = tuple(
        field_name for field_name in fieldnames if not field_name.startswith("LFQ intensity ")
    )
    dynamic_fields = tuple(
        field_name for field_name in fieldnames if field_name in selected_columns
    )
    return (*static_fields, *dynamic_fields)


def _render_tabular_rows(
    *,
    rows: list[dict[str, str]],
    fieldnames: tuple[str, ...],
) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field_name: row.get(field_name, "") for field_name in fieldnames})
    return buffer.getvalue()


def _nonempty(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


__all__ = [
    "PublicBenchmarkSubsetCountRange",
    "PublicBenchmarkSubsetInput",
    "PublicBenchmarkSubsetReport",
    "build_public_benchmark_subset",
]
