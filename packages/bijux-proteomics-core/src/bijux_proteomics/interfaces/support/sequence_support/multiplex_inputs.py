# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401

"""Multiplex and SILAC input parsing helpers for interface workflows."""

from __future__ import annotations

from ..foundation import click
from ..multiplex_targeted import SilacLabel, TmtReporterChannelColumn


def _parse_tmt_channel_column_specs(
    specs: tuple[str, ...],
) -> tuple[TmtReporterChannelColumn, ...]:
    resolved: list[TmtReporterChannelColumn] = []
    for spec in specs:
        if "=" not in spec:
            raise click.ClickException("channel-column must use CHANNEL=COLUMN syntax")
        channel, column_name = spec.split("=", 1)
        channel = channel.strip()
        column_name = column_name.strip()
        if not channel or not column_name:
            raise click.ClickException("channel-column must use CHANNEL=COLUMN syntax")
        resolved.append(
            TmtReporterChannelColumn(
                multiplex_channel=channel,
                column_name=column_name,
            )
        )
    return tuple(resolved)


def _parse_silac_label_spec(spec: str) -> tuple[SilacLabel, ...]:
    labels = tuple(
        SilacLabel(token.strip().lower()) for token in spec.split(",") if token.strip()
    )
    if len(labels) < 2:
        raise click.ClickException("labels must name at least two SILAC label states")
    return labels
