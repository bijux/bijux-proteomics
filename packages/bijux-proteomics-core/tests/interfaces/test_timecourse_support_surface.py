# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.domain.errors import DesignError
from bijux_proteomics.interfaces.support.timecourse_support.timepoint_order import (
    _parse_timepoint_order_file,
)


def test_timepoint_order_file_requires_at_least_one_label(tmp_path: Path) -> None:
    empty_path = tmp_path / "timepoints.tsv"
    empty_path.write_text("# comment only\nlabel\n", encoding="utf-8")

    with pytest.raises(
        DesignError, match="timepoint order file must contain at least one label"
    ):
        _parse_timepoint_order_file(empty_path)
