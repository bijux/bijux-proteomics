# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Atomic file-write helpers for governed artifact outputs."""

from __future__ import annotations

import itertools
import os
from pathlib import Path
import shutil

_ATOMIC_WRITE_COUNTER = itertools.count()


def atomic_write_text(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """Write one text artifact by atomic replacement in the target directory."""

    atomic_write_bytes(path, text.encode(encoding))


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write one byte artifact by atomic replacement in the target directory."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = _reserve_temporary_path(path)
    try:
        with temporary_path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def atomic_copy_file(source_path: Path, destination_path: Path) -> None:
    """Copy one artifact by atomic replacement in the destination directory."""

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = _reserve_temporary_path(destination_path)
    try:
        with (
            source_path.open("rb") as source_handle,
            temporary_path.open("xb") as destination_handle,
        ):
            shutil.copyfileobj(source_handle, destination_handle)
            destination_handle.flush()
            os.fsync(destination_handle.fileno())
        os.replace(temporary_path, destination_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def _reserve_temporary_path(path: Path) -> Path:
    return path.with_name(
        f".{path.name}.bijux-write-{os.getpid()}-{next(_ATOMIC_WRITE_COUNTER)}.tmp"
    )


__all__ = [
    "atomic_copy_file",
    "atomic_write_bytes",
    "atomic_write_text",
    "os",
]
