# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import builtins

import pytest

from bijux_proteomics_foundation.outcomes.exceptions import (
    MissingOptionalDependencyError,
)
from bijux_proteomics_foundation.outcomes.optional_dependencies import (
    import_optional_module,
    is_missing_optional_dependency_error,
)


def test_missing_optional_dependency_error_explains_install_hint() -> None:
    error = MissingOptionalDependencyError(
        dependency_name="pyarrow",
        feature_name="parquet peptide export",
        install_hint="pip install bijux-proteomics-core[parquet]",
    )

    assert "parquet peptide export requires optional dependency 'pyarrow'" in str(error)
    assert "bijux-proteomics-core[parquet]" in str(error)


def test_import_optional_module_raises_stable_optional_dependency_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "pyarrow" or name.startswith("pyarrow."):
            raise ModuleNotFoundError("No module named 'pyarrow'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(MissingOptionalDependencyError, match="pyarrow"):
        import_optional_module(
            "pyarrow",
            dependency_name="pyarrow",
            feature_name="parquet peptide export",
            install_hint="pip install bijux-proteomics-core[parquet]",
        )


def test_optional_dependency_error_detection_rejects_unrelated_import_failures() -> None:
    error = ModuleNotFoundError("No module named 'totally_unrelated'")

    assert not is_missing_optional_dependency_error(
        error,
        import_roots=("pyarrow",),
    )
