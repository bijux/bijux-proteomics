# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Descriptor contracts for package-owned shipped public benchmark datasets."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field, ValidationError, model_validator
import yaml

from bijux_proteomics.domain.errors import (
    DesignError,
    InvalidWorkflowError,
    SchemaError,
)
from bijux_proteomics.io.formats import ExperimentalDesignSampleRole
from bijux_proteomics_foundation import JsonModel


class PublicBenchmarkSearchEngine(StrEnum):
    """Stable workflow-family identifiers accepted by public descriptors."""

    DIANN = "diann"
    LFQ = "lfq"
    MAXQUANT = "maxquant"
    FRAGPIPE = "fragpipe"
    PTM = "ptm"
    TMT = "tmt"
    TARGETED = "targeted"


class PublicBenchmarkSourceFile(JsonModel):
    """One governed input file declared by a public benchmark descriptor."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1)
    schema_id: str = Field(..., min_length=1)
    repo_relative_path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    public_reference_url: str | None = None
    note: str | None = None


class PublicBenchmarkSampleGroup(JsonModel):
    """One biological or technical group declared by a benchmark descriptor."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str | None = None


class PublicBenchmarkSampleMetadata(JsonModel):
    """One declared sample row that should match the runnable design surface."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    group_id: str = Field(..., min_length=1)
    condition: str | None = None
    replicate: int | None = Field(default=None, ge=1)
    fraction: int | None = Field(default=None, ge=1)
    spectra_file: str | None = None
    identifications_file: str | None = None
    batch: str | None = None
    instrument: str | None = None
    search_engine: str | None = None
    multiplex_group: str | None = None
    multiplex_channel: str | None = None
    sample_role: ExperimentalDesignSampleRole | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    note: str | None = None


class PublicBenchmarkContrast(JsonModel):
    """One named contrast over declared benchmark sample groups."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    note: str | None = None


class PublicBenchmarkApproximateCount(JsonModel):
    """One approximate count expectation checked against workflow summary output."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str = Field(..., min_length=1)
    expected: int = Field(..., ge=0)
    tolerance: int = Field(default=0, ge=0)


class PublicBenchmarkExpectedSignalSubjectKind(StrEnum):
    """Stable biological entity kinds checked after a successful benchmark run."""

    PROTEIN = "protein"
    PATHWAY = "pathway"
    PTM_SITE = "ptm_site"


class PublicBenchmarkExpectedSignalDirection(StrEnum):
    """Stable expectation kinds over benchmark biological signal checks."""

    UP = "up"
    DOWN = "down"
    PRESENT = "present"


class PublicBenchmarkExpectedBiologicalSignal(JsonModel):
    """One expected biological signal for a real dataset benchmark."""

    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(..., min_length=1)
    subject_kind: PublicBenchmarkExpectedSignalSubjectKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str | None = None
    expected_direction: PublicBenchmarkExpectedSignalDirection
    max_adjusted_p_value: float | None = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_effect_size: float | None = Field(default=None, ge=0.0)
    note: str | None = None


class PublicBenchmarkKnownLimitationSeverity(StrEnum):
    """Stable severity classes for shipped public benchmark limitations."""

    ADVISORY = "advisory"
    BLOCKING = "blocking"


class PublicBenchmarkKnownLimitation(JsonModel):
    """One explicit known limitation carried by a shipped public descriptor."""

    model_config = ConfigDict(extra="forbid")

    limitation_id: str = Field(..., min_length=1)
    severity: PublicBenchmarkKnownLimitationSeverity
    affected_surface: str = Field(..., min_length=1)
    blocks_workflow_execution: bool = False
    description: str = Field(..., min_length=1)
    note: str | None = None


class PublicBenchmarkCommand(JsonModel):
    """One reviewer-facing command description for a benchmark descriptor."""

    model_config = ConfigDict(extra="forbid")

    cli: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)


class PublicBenchmarkOutputCheck(JsonModel):
    """One output existence check evaluated after successful workflow execution."""

    model_config = ConfigDict(extra="forbid")

    output_id: str = Field(..., min_length=1)
    relative_path: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class PublicBenchmarkDescriptor(JsonModel):
    """Descriptor loaded from one package-owned ``benchmarks/public/<dataset>/dataset.yml``."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    accession: str = Field(..., min_length=1)
    species: str = Field(..., min_length=1)
    search_engine: PublicBenchmarkSearchEngine
    source_files: tuple[PublicBenchmarkSourceFile, ...] = Field(default_factory=tuple)
    expected_input_schemas: tuple[str, ...] = Field(default_factory=tuple)
    sample_groups: tuple[PublicBenchmarkSampleGroup, ...] = Field(default_factory=tuple)
    sample_metadata: tuple[PublicBenchmarkSampleMetadata, ...] = Field(
        default_factory=tuple
    )
    contrast: PublicBenchmarkContrast
    expected_approximate_counts: tuple[PublicBenchmarkApproximateCount, ...] = Field(
        default_factory=tuple
    )
    expected_biological_signals: tuple[PublicBenchmarkExpectedBiologicalSignal, ...] = (
        Field(default_factory=tuple)
    )
    known_limitations: tuple[PublicBenchmarkKnownLimitation, ...] = Field(
        default_factory=tuple
    )
    command: PublicBenchmarkCommand
    output_checks: tuple[PublicBenchmarkOutputCheck, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_internal_consistency(self) -> PublicBenchmarkDescriptor:
        source_ids = [source.source_id for source in self.source_files]
        if len(source_ids) != len(set(source_ids)):
            raise SchemaError("descriptor source_ids must be unique")

        schema_ids = [source.schema_id for source in self.source_files]
        if len(schema_ids) != len(set(schema_ids)):
            raise SchemaError("descriptor source schema_ids must be unique")

        group_ids = [group.group_id for group in self.sample_groups]
        if len(group_ids) != len(set(group_ids)):
            raise DesignError("descriptor sample_groups must use unique group_ids")
        if self.contrast.condition_a not in set(group_ids):
            raise DesignError(
                "contrast condition_a must reference a declared sample_group"
            )
        if self.contrast.condition_b not in set(group_ids):
            raise DesignError(
                "contrast condition_b must reference a declared sample_group"
            )

        declared_group_sample_ids: dict[str, tuple[str, ...]] = {
            group.group_id: group.sample_ids for group in self.sample_groups
        }
        flat_group_sample_ids = [
            sample_id
            for sample_ids in declared_group_sample_ids.values()
            for sample_id in sample_ids
        ]
        if len(flat_group_sample_ids) != len(set(flat_group_sample_ids)):
            raise DesignError(
                "descriptor sample_groups cannot reuse one sample_id twice"
            )

        metadata_sample_ids = [sample.sample_id for sample in self.sample_metadata]
        if len(metadata_sample_ids) != len(set(metadata_sample_ids)):
            raise DesignError("descriptor sample_metadata must use unique sample_ids")
        for sample in self.sample_metadata:
            if sample.group_id not in declared_group_sample_ids:
                raise DesignError(
                    "descriptor sample_metadata group_id must reference a declared sample_group"
                )

        if self.sample_metadata:
            metadata_by_group: dict[str, list[str]] = {}
            for sample in self.sample_metadata:
                metadata_by_group.setdefault(sample.group_id, []).append(
                    sample.sample_id
                )
            for group_id, sample_ids in declared_group_sample_ids.items():
                metadata_sample_ids_for_group = tuple(
                    sorted(metadata_by_group.get(group_id, ()))
                )
                if tuple(sorted(sample_ids)) != metadata_sample_ids_for_group:
                    raise DesignError(
                        "descriptor sample_groups and sample_metadata must declare the "
                        "same sample_ids for each group"
                    )

        signal_ids = [signal.signal_id for signal in self.expected_biological_signals]
        if len(signal_ids) != len(set(signal_ids)):
            raise SchemaError(
                "descriptor expected_biological_signals must use unique ids"
            )

        limitation_ids = [item.limitation_id for item in self.known_limitations]
        if len(limitation_ids) != len(set(limitation_ids)):
            raise SchemaError("descriptor known_limitations must use unique ids")

        return self


def load_public_benchmark_descriptor(
    descriptor_path: Path,
) -> PublicBenchmarkDescriptor:
    """Load and validate one public benchmark descriptor."""

    try:
        payload = yaml.safe_load(descriptor_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SchemaError(
            f"public benchmark descriptor YAML is invalid: {descriptor_path}"
        ) from exc
    try:
        return PublicBenchmarkDescriptor.model_validate(payload)
    except ValidationError as exc:
        raise SchemaError(
            f"public benchmark descriptor payload is invalid: {descriptor_path}"
        ) from exc


def public_benchmark_root() -> Path:
    """Return the package-owned root for shipped public benchmark descriptors."""

    return Path(__file__).resolve().parents[3] / "benchmarks" / "public"


def resolve_public_benchmark_path(benchmark_path: Path | str | None = None) -> Path:
    """Resolve a reviewer-supplied benchmark path onto the package-owned tree."""

    package_root = public_benchmark_root()
    if benchmark_path is None:
        return package_root
    candidate = Path(benchmark_path)
    normalized = candidate.as_posix().rstrip("/")
    if normalized in {"benchmarks/public", "./benchmarks/public"}:
        return package_root
    prefix = "benchmarks/public/"
    if normalized.startswith(prefix):
        return package_root / normalized.removeprefix(prefix)
    if normalized.startswith(f"./{prefix}"):
        return package_root / normalized.removeprefix(f"./{prefix}")
    if candidate.exists():
        return candidate

    repo_root = package_root.parents[3]
    repo_relative_prefix = repo_root / "benchmarks" / "public"
    if candidate.is_absolute() and candidate == repo_relative_prefix:
        return package_root
    if candidate.is_absolute() and repo_relative_prefix in candidate.parents:
        return package_root / candidate.relative_to(repo_relative_prefix)
    raise FileNotFoundError(
        "public benchmark path does not exist: "
        f"{candidate}. Use the package-owned benchmark root at {package_root}."
    )


def resolve_public_benchmark_root(benchmark_root: Path | str | None = None) -> Path:
    """Resolve a reviewer-supplied benchmark root onto the package-owned tree."""

    resolved = resolve_public_benchmark_path(benchmark_root)
    if resolved.is_file():
        raise InvalidWorkflowError(
            "public benchmark root must be a directory, not a descriptor path: "
            f"{resolved}"
        )
    if not resolved.exists():
        raise FileNotFoundError(
            "public benchmark root does not exist: "
            f"{resolved}. Use the package-owned benchmark root at {public_benchmark_root()}."
        )
    return resolved


def list_public_benchmark_descriptor_paths(benchmark_root: Path) -> tuple[Path, ...]:
    """List every descriptor rooted under the package-owned benchmark tree."""

    return tuple(sorted(benchmark_root.glob("*/dataset.yml")))


__all__ = [
    "PublicBenchmarkApproximateCount",
    "PublicBenchmarkCommand",
    "PublicBenchmarkContrast",
    "PublicBenchmarkDescriptor",
    "PublicBenchmarkExpectedBiologicalSignal",
    "PublicBenchmarkExpectedSignalDirection",
    "PublicBenchmarkExpectedSignalSubjectKind",
    "PublicBenchmarkKnownLimitation",
    "PublicBenchmarkKnownLimitationSeverity",
    "PublicBenchmarkOutputCheck",
    "PublicBenchmarkSampleGroup",
    "PublicBenchmarkSampleMetadata",
    "PublicBenchmarkSearchEngine",
    "PublicBenchmarkSourceFile",
    "public_benchmark_root",
    "resolve_public_benchmark_path",
    "resolve_public_benchmark_root",
    "list_public_benchmark_descriptor_paths",
    "load_public_benchmark_descriptor",
]
