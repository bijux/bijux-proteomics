# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
TUTORIAL_PATH = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-runtime"
    / "docs"
    / "ADVANCED-DIANN-PYTHON-API.md"
)


def _python_blocks(text: str) -> tuple[str, ...]:
    return tuple(
        block.strip()
        for block in re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)
    )


def test_advanced_diann_python_api_tutorial_executes(tmp_path: Path) -> None:
    text = TUTORIAL_PATH.read_text(encoding="utf-8")
    blocks = _python_blocks(text)

    assert "archive_completed_advanced_diann_run" in text
    assert "load_completed_run" in text
    assert blocks, "advanced DIA-NN Python API tutorial must contain one python example"

    globals_dict = {
        "__name__": "__advanced_diann_python_tutorial__",
        "REPO_ROOT": REPO_ROOT,
        "TMP_PATH": tmp_path,
    }
    for index, block in enumerate(blocks, start=1):
        exec(
            compile(
                block,
                f"{TUTORIAL_PATH.relative_to(REPO_ROOT).as_posix()}::python_example_{index}",
                "exec",
            ),
            globals_dict,
            globals_dict,
        )
