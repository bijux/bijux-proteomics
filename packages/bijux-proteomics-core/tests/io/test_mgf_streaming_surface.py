# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from collections.abc import Iterator
from itertools import islice
from pathlib import Path
from types import TracebackType
from typing import TextIO, cast

from pytest import MonkeyPatch

from bijux_proteomics.io.mgf_streaming import (
    count_mgf_blocks,
    iter_mgf_parse_results,
    iter_mgf_spectra,
    parse_mgf,
)


def _spectra_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "spectra" / name


def test_iter_mgf_parse_results_preserves_accepted_and_rejected_blocks() -> None:
    results = tuple(iter_mgf_parse_results(_spectra_fixture("malformed.mgf")))

    assert len(results) == 2
    assert results[0].accepted_spectrum is None
    assert results[0].rejected_block is not None
    assert results[1].accepted_spectrum is None
    assert results[1].rejected_block is not None
    issue_codes = {
        issue.code
        for result in results
        for block in [result.rejected_block]
        if block is not None
        for issue in block.issues
    }
    assert "missing_precursor_mz" in issue_codes
    assert "missing_end_ions" in issue_codes


def test_iter_mgf_spectra_yields_early_for_generated_large_mgf(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    path = tmp_path / "large_streaming_input.mgf"
    with path.open("w", encoding="utf-8") as handle:
        for index in range(1, 5001):
            handle.write("BEGIN IONS\n")
            handle.write(f"SCANS=scan={index}\n")
            handle.write(f"TITLE=streamed spectrum {index}\n")
            handle.write(f"PEPMASS={400.0 + index / 1000.0:.4f}\n")
            handle.write("CHARGE=2+\n")
            handle.write(f"RTINSECONDS={10.0 + index:.2f}\n")
            handle.write("100.0 10.0\n")
            handle.write("200.0 20.0\n")
            handle.write("END IONS\n")

    original_open = Path.open
    line_counter = {"count": 0}

    class _StreamingHandle:
        def __init__(self, wrapped: TextIO) -> None:
            self._wrapped = wrapped

        def __iter__(self) -> Iterator[str]:
            for line in self._wrapped:
                line_counter["count"] += 1
                yield line

        def __enter__(self) -> _StreamingHandle:
            self._wrapped.__enter__()
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool | None:
            return self._wrapped.__exit__(exc_type, exc, tb)

        def read(self, *args: object, **kwargs: object) -> str:
            raise AssertionError("iter_mgf_spectra should not call read()")

        def readlines(self, *args: object, **kwargs: object) -> list[str]:
            raise AssertionError("iter_mgf_spectra should not call readlines()")

        def __getattr__(self, name: str) -> object:
            return getattr(self._wrapped, name)

    def _wrapped_open(
        self: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> TextIO:
        handle = original_open(
            self,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )
        if self == path:
            return cast(TextIO, _StreamingHandle(cast(TextIO, handle)))
        return cast(TextIO, handle)

    monkeypatch.setattr(Path, "open", _wrapped_open)

    iterator = iter_mgf_spectra(path)
    first = next(iterator)
    next_four = tuple(islice(iterator, 4))

    assert first.spectrum_id == "scan=1"
    assert len(next_four) == 4
    assert next_four[-1].spectrum_id == "scan=5"
    assert line_counter["count"] < 60
    assert count_mgf_blocks(path) == 5000


def test_parse_mgf_aggregates_streamed_results() -> None:
    report = parse_mgf(_spectra_fixture("multi.mgf"))

    assert report.total_blocks == 2
    assert len(report.accepted_spectra) == 2
    assert len(report.rejected_blocks) == 0
