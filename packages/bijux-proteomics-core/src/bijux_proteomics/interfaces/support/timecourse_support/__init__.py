# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401

"""Compatibility facade for time-course support helper ownership."""

from __future__ import annotations

from .timepoint_order import _parse_timepoint_order_file

__all__ = ("_parse_timepoint_order_file",)
