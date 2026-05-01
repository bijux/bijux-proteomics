# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Study metadata and lab handoff surfaces for iteration 08."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class StudyMetadataRecord(JsonModel):
    """One normalized study metadata row connecting sample and run context."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    cohort_id: str = Field(..., min_length=1)
    condition_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    replicate_id: str = Field(..., min_length=1)
    fraction_id: str = Field(..., min_length=1)
    instrument_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)


class StudyMetadataModel(JsonModel):
    """Stable collection of normalized study metadata records."""

    model_config = ConfigDict(extra="forbid")

    records: tuple[StudyMetadataRecord, ...] = Field(default_factory=tuple)
    study_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)


def build_study_metadata_model(
    records: tuple[StudyMetadataRecord, ...],
) -> StudyMetadataModel:
    """Build study metadata model with deterministic collection summaries."""
    return StudyMetadataModel(
        records=records,
        study_count=len({record.study_id for record in records}),
        sample_count=len({record.sample_id for record in records}),
        run_count=len({record.run_id for record in records}),
    )
