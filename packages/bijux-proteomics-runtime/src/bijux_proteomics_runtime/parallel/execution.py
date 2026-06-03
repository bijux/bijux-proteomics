# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic parallel execution over runtime-owned file materialization steps."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from enum import StrEnum
import hashlib
import io
import json
from pathlib import Path
import time
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.support.workspace import write_text_atomic


class ParallelStepFileFormat(StrEnum):
    """Stable file formats emitted by deterministic parallel steps."""

    JSON = "json"
    TSV = "tsv"


class ParallelStepFile(JsonModel):
    """One file written by a deterministic parallel runtime step."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    format: ParallelStepFileFormat
    columns: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    json_payload: dict[str, Any] | list[Any] | None = None

    @model_validator(mode="after")
    def _validate_file(self) -> ParallelStepFile:
        if self.format is ParallelStepFileFormat.TSV:
            if not self.columns:
                raise ValueError("tsv parallel step files require explicit columns")
            if self.json_payload is not None:
                raise ValueError("tsv parallel step files cannot carry json_payload")
            unexpected_columns = {
                key for row in self.rows for key in row if key not in self.columns
            }
            if unexpected_columns:
                raise ValueError(
                    "tsv parallel step file rows contain undeclared columns: "
                    + ", ".join(sorted(unexpected_columns))
                )
        else:
            if self.json_payload is None:
                raise ValueError("json parallel step files require json_payload")
            if self.columns or self.rows:
                raise ValueError(
                    "json parallel step files cannot carry tsv columns or rows"
                )
        return self


class ParallelStep(JsonModel):
    """One deterministic runtime step that may execute in parallel with peers."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    output_files: tuple[ParallelStepFile, ...] = Field(default_factory=tuple)
    simulated_delay_ms: int = Field(default=0, ge=0, le=10_000)

    @model_validator(mode="after")
    def _validate_step(self) -> ParallelStep:
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError("parallel step dependencies must be unique")
        output_paths = [artifact.path for artifact in self.output_files]
        if len(set(output_paths)) != len(output_paths):
            raise ValueError("parallel step output paths must be unique within a step")
        return self


class ParallelStepArtifact(JsonModel):
    """One deterministic output file written by a parallel runtime step."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    byte_count: int = Field(..., ge=0)
    row_count: int = Field(..., ge=0)


class ParallelStepResult(JsonModel):
    """One deterministic step result emitted by the parallel runtime owner."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    artifacts: tuple[ParallelStepArtifact, ...] = Field(default_factory=tuple)


class ParallelRunGroup(JsonModel):
    """One deterministic dependency group executed as a parallel wave."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    step_ids: tuple[str, ...] = Field(default_factory=tuple)


class ParallelRunReport(JsonModel):
    """Stable report over deterministic serial or parallel step execution."""

    model_config = ConfigDict(extra="forbid")

    workers: int = Field(..., ge=1)
    groups: tuple[ParallelRunGroup, ...] = Field(default_factory=tuple)
    step_results: tuple[ParallelStepResult, ...] = Field(default_factory=tuple)


def _serialize_step_file(file: ParallelStepFile) -> str:
    if file.format is ParallelStepFileFormat.JSON:
        return json.dumps(file.json_payload, indent=2, sort_keys=True) + "\n"
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(file.columns),
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in file.rows:
        writer.writerow(
            {
                column: "" if row.get(column) is None else row.get(column, "")
                for column in file.columns
            }
        )
    return buffer.getvalue()


def _sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _execute_step(step: ParallelStep) -> ParallelStepResult:
    if step.simulated_delay_ms:
        time.sleep(step.simulated_delay_ms / 1000.0)
    artifacts: list[ParallelStepArtifact] = []
    for file in sorted(step.output_files, key=lambda artifact: artifact.path):
        payload = _serialize_step_file(file)
        path = Path(file.path)
        write_text_atomic(path, payload)
        artifacts.append(
            ParallelStepArtifact(
                path=str(path),
                sha256=_sha256_text(payload),
                byte_count=len(payload.encode("utf-8")),
                row_count=len(file.rows),
            )
        )
    return ParallelStepResult(step_id=step.step_id, artifacts=tuple(artifacts))


def _build_parallel_groups(
    steps: tuple[ParallelStep, ...],
) -> tuple[ParallelRunGroup, ...]:
    step_by_id = {step.step_id: step for step in steps}
    if len(step_by_id) != len(steps):
        raise ValueError("parallel step ids must be unique")
    output_paths = [artifact.path for step in steps for artifact in step.output_files]
    if len(set(output_paths)) != len(output_paths):
        raise ValueError("parallel steps cannot write the same output file path")
    unresolved = set(step_by_id)
    levels: dict[str, int] = {}
    while unresolved:
        progressed = False
        for step_id in sorted(unresolved):
            step = step_by_id[step_id]
            missing_dependencies = [
                dependency
                for dependency in step.depends_on
                if dependency not in step_by_id
            ]
            if missing_dependencies:
                raise ValueError(
                    "parallel step dependencies must reference known step ids: "
                    + ", ".join(missing_dependencies)
                )
            if all(dependency in levels for dependency in step.depends_on):
                levels[step_id] = (
                    0
                    if not step.depends_on
                    else max(levels[dependency] for dependency in step.depends_on) + 1
                )
                unresolved.remove(step_id)
                progressed = True
        if not progressed:
            raise ValueError(
                "parallel steps contain a cycle and cannot be executed deterministically"
            )
    grouped: dict[int, list[str]] = {}
    for step_id, level in levels.items():
        grouped.setdefault(level, []).append(step_id)
    return tuple(
        ParallelRunGroup(
            group_id=f"parallel-group-{level}",
            step_ids=tuple(sorted(step_ids)),
        )
        for level, step_ids in sorted(grouped.items())
    )


def run_parallel_steps(
    steps: tuple[ParallelStep, ...],
    workers: int,
) -> ParallelRunReport:
    """Execute deterministic step waves so serial and parallel outputs stay byte-identical."""
    if workers < 1:
        raise ValueError("workers must be >= 1")

    groups = _build_parallel_groups(steps)
    step_by_id = {step.step_id: step for step in steps}
    results: list[ParallelStepResult] = []
    for group in groups:
        if workers == 1 or len(group.step_ids) == 1:
            for step_id in group.step_ids:
                results.append(_execute_step(step_by_id[step_id]))
            continue
        group_results: list[ParallelStepResult] = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_by_step_id = {
                step_id: executor.submit(_execute_step, step_by_id[step_id])
                for step_id in group.step_ids
            }
            for future in as_completed(tuple(future_by_step_id.values())):
                group_results.append(future.result())
        results.extend(sorted(group_results, key=lambda result: result.step_id))
    return ParallelRunReport(
        workers=workers,
        groups=groups,
        step_results=tuple(results),
    )


__all__ = [
    "ParallelRunGroup",
    "ParallelRunReport",
    "ParallelStep",
    "ParallelStepArtifact",
    "ParallelStepFile",
    "ParallelStepFileFormat",
    "ParallelStepResult",
    "run_parallel_steps",
]
