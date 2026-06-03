# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Laboratory-facing contamination source classification."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ContaminantClass(StrEnum):
    """Stable contaminant source classes for laboratory review."""

    KERATIN = "keratin"
    ENZYME = "enzyme"
    STANDARD = "standard"
    UNKNOWN = "unknown"
    MIXED = "mixed"


class ContaminantEvidenceEntry(JsonModel):
    """One sample-level contaminant protein burden row."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    sample_total_intensity: float = Field(..., gt=0.0)


class ContaminantAnnotationEntry(JsonModel):
    """One contaminant annotation row mapping proteins to a stable source class."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    contaminant_class: ContaminantClass


class ContaminationClassificationEntry(JsonModel):
    """One sample-level contamination source classification."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    contaminant_class: ContaminantClass
    top_contaminant_proteins: tuple[str, ...] = Field(default_factory=tuple)
    intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    action_hint: str = Field(..., min_length=1)


def classify_contamination(
    contaminant_evidence: tuple[ContaminantEvidenceEntry, ...],
    contaminant_annotation: tuple[ContaminantAnnotationEntry, ...],
) -> tuple[ContaminationClassificationEntry, ...]:
    """Classify dominant contamination sources for each sample."""

    if not contaminant_evidence:
        return ()
    annotation_by_protein = _annotation_lookup(contaminant_annotation)
    rows_by_sample: dict[str, list[ContaminantEvidenceEntry]] = {}
    for row in contaminant_evidence:
        rows_by_sample.setdefault(row.sample_id, []).append(row)
    return tuple(
        _classify_sample(
            sample_id, tuple(rows_by_sample[sample_id]), annotation_by_protein
        )
        for sample_id in sorted(rows_by_sample)
    )


def render_contamination_classification_tsv(
    entries: tuple[ContaminationClassificationEntry, ...],
) -> str:
    """Render contamination classifications as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "contaminant_class",
            "top_contaminant_proteins",
            "intensity_fraction",
            "action_hint",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.sample_id,
                entry.contaminant_class.value,
                ";".join(entry.top_contaminant_proteins),
                f"{entry.intensity_fraction:.4f}",
                entry.action_hint,
            )
        )
    return buffer.getvalue()


def _annotation_lookup(
    rows: tuple[ContaminantAnnotationEntry, ...],
) -> dict[str, ContaminantClass]:
    lookup: dict[str, ContaminantClass] = {}
    for row in rows:
        existing = lookup.get(row.protein_ref)
        if existing is not None and existing is not row.contaminant_class:
            raise ValueError(
                f"contaminant_annotation assigns conflicting classes for {row.protein_ref!r}"
            )
        lookup[row.protein_ref] = row.contaminant_class
    return lookup


def _classify_sample(
    sample_id: str,
    rows: tuple[ContaminantEvidenceEntry, ...],
    annotation_by_protein: dict[str, ContaminantClass],
) -> ContaminationClassificationEntry:
    sample_total_intensity = rows[0].sample_total_intensity
    if any(row.sample_total_intensity != sample_total_intensity for row in rows):
        raise ValueError(
            f"sample {sample_id!r} must carry one consistent sample_total_intensity"
        )

    class_intensity: dict[ContaminantClass, float] = {}
    protein_intensity: dict[str, float] = {}
    for row in rows:
        contaminant_class = annotation_by_protein.get(
            row.protein_ref,
            ContaminantClass.UNKNOWN,
        )
        class_intensity[contaminant_class] = (
            class_intensity.get(contaminant_class, 0.0) + row.intensity
        )
        protein_intensity[row.protein_ref] = (
            protein_intensity.get(row.protein_ref, 0.0) + row.intensity
        )

    total_contaminant_intensity = sum(protein_intensity.values())
    intensity_fraction = (
        0.0
        if sample_total_intensity <= 0.0
        else min(1.0, total_contaminant_intensity / sample_total_intensity)
    )

    ranked_classes = sorted(
        class_intensity.items(),
        key=lambda item: (-item[1], item[0].value),
    )
    dominant_class, dominant_intensity = ranked_classes[0]
    if len(ranked_classes) > 1 and ranked_classes[1][1] >= dominant_intensity * 0.75:
        assigned_class = ContaminantClass.MIXED
    else:
        assigned_class = dominant_class

    top_proteins = tuple(
        protein
        for protein, _ in sorted(
            protein_intensity.items(),
            key=lambda item: (-item[1], item[0]),
        )[:3]
    )
    return ContaminationClassificationEntry(
        sample_id=sample_id,
        contaminant_class=assigned_class,
        top_contaminant_proteins=top_proteins,
        intensity_fraction=round(intensity_fraction, 4),
        action_hint=_action_hint(assigned_class),
    )


def _action_hint(contaminant_class: ContaminantClass) -> str:
    hints = {
        ContaminantClass.KERATIN: "audit sample handling and exposed surfaces for skin or dust contamination",
        ContaminantClass.ENZYME: "review digestion cleanup and enzyme carry-through controls",
        ContaminantClass.STANDARD: "check spike-in or loading-standard handling and dilution records",
        ContaminantClass.UNKNOWN: "review unmatched contaminant proteins and expand annotation coverage",
        ContaminantClass.MIXED: "review multiple contaminant sources before accepting sample-level interpretation",
    }
    return hints[contaminant_class]


__all__ = [
    "ContaminantAnnotationEntry",
    "ContaminantClass",
    "ContaminantEvidenceEntry",
    "ContaminationClassificationEntry",
    "classify_contamination",
    "render_contamination_classification_tsv",
]
