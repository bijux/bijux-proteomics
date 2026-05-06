from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_dev.security.trusted_process import run_text


def test_trusted_process_rejects_relative_executables() -> None:
    with pytest.raises(ValueError, match="absolute executable path"):
        run_text(("python3", "--version"), check=False)


def test_trusted_process_accepts_absolute_executables() -> None:
    completed = run_text((Path("/usr/bin/env"), "true"), check=True)

    assert completed.returncode == 0
