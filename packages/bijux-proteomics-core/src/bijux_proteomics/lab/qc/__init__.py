# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed LC-MS quality-control facade."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.lab.public_api import (
    QC_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
    module_directory,
    resolve_public_export,
)
from bijux_proteomics.lab.qc.support import stable_sha256

__all__, _QC_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(QC_FACADE_OWNERS)
)

_stable_sha256 = stable_sha256


def __getattr__(name: str) -> Any:
    return resolve_public_export(__name__, globals(), _QC_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
