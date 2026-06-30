# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.domain as domain
from bijux_proteomics.domain.public_api import (
    DOMAIN_FACADE_BUDGET,
    build_domain_export_owner_map,
    list_domain_export_names,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def _non_empty_line_count(relative_path: str) -> int:
    content = (REPO_ROOT / relative_path).read_text(encoding="utf-8").splitlines()
    return sum(1 for line in content if line.strip())


def test_domain_facade_exports_match_governed_public_api() -> None:
    expected = list_domain_export_names()

    assert tuple(domain.__all__) == expected
    assert len(domain.__all__) <= DOMAIN_FACADE_BUDGET.max_public_symbols
    assert len(build_domain_export_owner_map()) == len(domain.__all__)
    assert "_res3_to1" not in domain.__all__

    for export_name in expected:
        assert hasattr(domain, export_name), export_name


def test_domain_facade_init_stays_within_budget() -> None:
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/domain/__init__.py"
    ) <= DOMAIN_FACADE_BUDGET.max_init_lines
