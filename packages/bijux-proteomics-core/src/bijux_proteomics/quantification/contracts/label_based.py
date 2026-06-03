# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.quantification.core_matrix import (
    quant_matrix_to_dense_array,
    rebuild_quant_matrix_from_dense_array,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel

if TYPE_CHECKING:
    pass


from .input_models import (
    LabelBasedChannelRole,
    MissingChannelPolicy,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
)
from .matrix_building import (
    _default_label_channel_role,
    _multiplex_channel_lookup,
    _rebuild_table_from_matrix,
    _table_matrix,
)
from .matrix_models import LabelFreeQuantTable


class LabelBasedChannelPolicyEntry(JsonModel):
    """One expected multiplex channel role inside a label-based assay policy."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    channel_role: LabelBasedChannelRole


class LabelBasedQuantPolicy(JsonModel):
    """Explicit channel-role and missing-channel policy for multiplex assays."""

    model_config = ConfigDict(extra="forbid")

    missing_channel_policy: MissingChannelPolicy = MissingChannelPolicy.ERROR
    channel_entries: tuple[LabelBasedChannelPolicyEntry, ...] = Field(
        default_factory=tuple
    )


class LabelBasedChannelStateEntry(JsonModel):
    """One observed or expected multiplex channel inside a label-based workflow."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    sample_role: ExperimentalDesignSampleRole | None = None
    channel_role: LabelBasedChannelRole
    present_in_design: bool
    present_in_table: bool
    note: str = Field(..., min_length=1)


class MissingMultiplexChannelEntry(JsonModel):
    """One missing multiplex channel handled under an explicit policy."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    expected_role: LabelBasedChannelRole
    policy: MissingChannelPolicy
    message: str = Field(..., min_length=1)


class LabelBasedQuantBundle(JsonModel):
    """Reviewable channel-level manifest for one label-based quantification table."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    normalization_method: NormalizationMethod
    policy: LabelBasedQuantPolicy
    channels: tuple[LabelBasedChannelStateEntry, ...] = Field(default_factory=tuple)
    missing_channels: tuple[MissingMultiplexChannelEntry, ...] = Field(
        default_factory=tuple
    )


class MultiplexNormalizationPolicy(JsonModel):
    """Normalization and balance settings for multiplex quantification groups."""

    model_config = ConfigDict(extra="forbid")

    method: NormalizationMethod = NormalizationMethod.MEDIAN
    balance_ratio_threshold: float = Field(default=1.5, ge=1.0)


class MultiplexChannelBalanceEntry(JsonModel):
    """One multiplex-channel abundance balance row within a single plex group."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    channel_role: LabelBasedChannelRole
    total_abundance: float = Field(..., ge=0.0)
    ratio_to_group_median: float = Field(..., ge=0.0)
    flagged: bool


class MultiplexChannelBalanceReport(JsonModel):
    """Governed channel-balance report across multiplex assay groups."""

    model_config = ConfigDict(extra="forbid")

    policy: MultiplexNormalizationPolicy
    entries: tuple[MultiplexChannelBalanceEntry, ...] = Field(default_factory=tuple)


def build_label_based_quant_bundle(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: LabelBasedQuantPolicy,
) -> LabelBasedQuantBundle:
    """Build a stable multiplex-channel manifest over a label-based quant table."""
    multiplex_entries = tuple(
        entry
        for entry in design_entries
        if entry.multiplex_group and entry.multiplex_channel
    )
    if not multiplex_entries:
        raise ValueError("label-based quantification requires multiplex design entries")
    if not policy.channel_entries:
        raise ValueError(
            "label-based quantification requires explicit expected channel policy entries"
        )

    design_lookup = {
        (entry.multiplex_group or "", entry.multiplex_channel or ""): entry
        for entry in multiplex_entries
    }
    table_sample_ids = set(table.sample_ids)
    channel_policy_lookup = {
        (entry.multiplex_group, entry.multiplex_channel): entry.channel_role
        for entry in policy.channel_entries
    }

    channels: list[LabelBasedChannelStateEntry] = []
    missing_channels: list[MissingMultiplexChannelEntry] = []

    seen_keys = sorted(set(design_lookup) | set(channel_policy_lookup))
    for multiplex_group, multiplex_channel in seen_keys:
        design_entry = design_lookup.get((multiplex_group, multiplex_channel))
        channel_role = channel_policy_lookup.get(
            (multiplex_group, multiplex_channel),
            _default_label_channel_role(design_entry)
            if design_entry is not None
            else LabelBasedChannelRole.SAMPLE,
        )
        present_in_design = design_entry is not None
        present_in_table = (
            design_entry.sample_id in table_sample_ids
            if design_entry is not None
            else False
        )
        if not present_in_design or not present_in_table:
            missing_channels.append(
                MissingMultiplexChannelEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    expected_role=channel_role,
                    policy=policy.missing_channel_policy,
                    message=(
                        "expected multiplex channel is absent from the design table"
                        if not present_in_design
                        else "design channel is present but has no quantification values in the table"
                    ),
                )
            )
            if policy.missing_channel_policy is MissingChannelPolicy.ERROR:
                raise ValueError(
                    "label-based quantification missing expected multiplex channel "
                    f"{multiplex_group}:{multiplex_channel}"
                )
        if (
            not present_in_design
            and policy.missing_channel_policy is MissingChannelPolicy.PRESERVE
        ):
            channels.append(
                LabelBasedChannelStateEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    sample_id=None,
                    condition=None,
                    sample_role=None,
                    channel_role=channel_role,
                    present_in_design=False,
                    present_in_table=False,
                    note="expected channel is preserved in the manifest even though it was not observed",
                )
            )
            continue
        if design_entry is None:
            continue
        if (
            not present_in_table
            and policy.missing_channel_policy is MissingChannelPolicy.PRESERVE
        ):
            note = "design channel is preserved even though no quantification values were observed"
        elif not present_in_table:
            note = (
                "design channel is represented as missing in the quantification table"
            )
        elif channel_role is LabelBasedChannelRole.CARRIER:
            note = "carrier channel remains explicit and is not silently treated as a biological sample"
        else:
            note = "observed multiplex channel is represented explicitly in the review manifest"
        channels.append(
            LabelBasedChannelStateEntry(
                multiplex_group=multiplex_group,
                multiplex_channel=multiplex_channel,
                sample_id=design_entry.sample_id,
                condition=design_entry.condition,
                sample_role=design_entry.sample_role,
                channel_role=channel_role,
                present_in_design=True,
                present_in_table=present_in_table,
                note=note,
            )
        )

    bundle = LabelBasedQuantBundle(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="label_based_quant_bundle",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        normalization_method=table.normalization_method,
        policy=policy,
        channels=tuple(
            sorted(
                channels,
                key=lambda entry: (entry.multiplex_group, entry.multiplex_channel),
            )
        ),
        missing_channels=tuple(
            sorted(
                missing_channels,
                key=lambda entry: (entry.multiplex_group, entry.multiplex_channel),
            )
        ),
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )


def normalize_multiplex_quant_table(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MultiplexNormalizationPolicy | None = None,
) -> LabelFreeQuantTable:
    """Normalize a multiplex quant table independently within each plex group."""
    if table.measure_kind is not QuantMeasureKind.INTENSITY:
        raise ValueError("multiplex normalization only applies to intensity tables")
    active_policy = policy or MultiplexNormalizationPolicy()
    multiplex_lookup = _multiplex_channel_lookup(design_entries)
    if not multiplex_lookup:
        raise ValueError("multiplex normalization requires multiplex design metadata")
    if active_policy.method is NormalizationMethod.NONE:
        quant_matrix = rebuild_quant_matrix_from_dense_array(
            table.to_quant_matrix(),
            quant_matrix_to_dense_array(table.to_quant_matrix()),
            transformation_step="normalization:none",
            metadata_updates={"normalization_method": NormalizationMethod.NONE.value},
        )
        return table.model_copy(
            update={
                "quant_matrix": quant_matrix,
                "normalization_method": NormalizationMethod.NONE,
                "normalization_factors": dict.fromkeys(table.sample_ids, 1.0),
            }
        )

    matrix, _ = _table_matrix(table)
    sample_index = {
        sample_id: index for index, sample_id in enumerate(table.sample_ids)
    }
    grouped_samples: dict[str, list[str]] = {}
    for sample_id in table.sample_ids:
        if sample_id not in multiplex_lookup:
            continue
        grouped_samples.setdefault(multiplex_lookup[sample_id][0], []).append(sample_id)
    if not grouped_samples:
        raise ValueError(
            "multiplex normalization requires at least one multiplex sample in the table"
        )

    normalized = matrix.copy()
    factors = dict.fromkeys(table.sample_ids, 1.0)
    for group_sample_ids in grouped_samples.values():
        if active_policy.method is NormalizationMethod.MEDIAN:
            sample_medians = {
                sample_id: float(np.nanmedian(matrix[:, sample_index[sample_id]]))
                if np.any(~np.isnan(matrix[:, sample_index[sample_id]]))
                else float("nan")
                for sample_id in group_sample_ids
            }
            finite_medians = [
                median
                for median in sample_medians.values()
                if math.isfinite(median) and median > 0
            ]
            group_median = (
                float(np.median(np.array(finite_medians, dtype=float)))
                if finite_medians
                else 1.0
            )
            for sample_id in group_sample_ids:
                sample_median = sample_medians[sample_id]
                factor = (
                    group_median / sample_median
                    if math.isfinite(sample_median) and sample_median > 0
                    else 1.0
                )
                factors[sample_id] = factor
                normalized[:, sample_index[sample_id]] = (
                    normalized[:, sample_index[sample_id]] * factor
                )
            continue
        raise ValueError(
            "multiplex normalization currently supports only explicit none or group-wise median normalization"
        )
    return _rebuild_table_from_matrix(
        table,
        normalized,
        normalization_method=active_policy.method,
        normalization_factors=factors,
    )


def build_multiplex_channel_balance_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MultiplexNormalizationPolicy | None = None,
) -> MultiplexChannelBalanceReport:
    """Build a channel-balance report over multiplex groups."""
    active_policy = policy or MultiplexNormalizationPolicy()
    multiplex_lookup = _multiplex_channel_lookup(design_entries)
    grouped_entries: dict[str, list[tuple[str, str, LabelBasedChannelRole, float]]] = {}
    for sample_id in table.sample_ids:
        multiplex_entry = multiplex_lookup.get(sample_id)
        if multiplex_entry is None:
            continue
        multiplex_group, multiplex_channel, channel_role = multiplex_entry
        total_abundance = float(
            sum(
                value.abundance or 0.0
                for value in table.values
                if value.sample_id == sample_id and value.abundance is not None
            )
        )
        grouped_entries.setdefault(multiplex_group, []).append(
            (sample_id, multiplex_channel, channel_role, total_abundance)
        )
    entries: list[MultiplexChannelBalanceEntry] = []
    for multiplex_group, bucket in sorted(grouped_entries.items()):
        totals = np.array([entry[3] for entry in bucket], dtype=float)
        group_median = float(np.median(totals)) if totals.size else 0.0
        for sample_id, multiplex_channel, channel_role, total_abundance in sorted(
            bucket,
            key=lambda entry: entry[1],
        ):
            ratio = (total_abundance / group_median) if group_median > 0 else 0.0
            entries.append(
                MultiplexChannelBalanceEntry(
                    multiplex_group=multiplex_group,
                    multiplex_channel=multiplex_channel,
                    sample_id=sample_id,
                    channel_role=channel_role,
                    total_abundance=total_abundance,
                    ratio_to_group_median=ratio,
                    flagged=(
                        ratio > active_policy.balance_ratio_threshold
                        or ratio < 1.0 / active_policy.balance_ratio_threshold
                    ),
                )
            )
    return MultiplexChannelBalanceReport(
        policy=active_policy,
        entries=tuple(
            sorted(
                entries,
                key=lambda entry: (entry.multiplex_group, entry.multiplex_channel),
            )
        ),
    )
