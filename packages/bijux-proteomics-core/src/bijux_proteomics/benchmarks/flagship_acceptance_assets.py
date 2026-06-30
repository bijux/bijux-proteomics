# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Refresh published flagship acceptance sheets."""

from __future__ import annotations

import argparse
from pathlib import Path

from bijux_proteomics.benchmarks.flagship.acceptance import (
    build_flagship_acceptance_dashboard,
    build_flagship_acceptance_history_ledger,
    build_flagship_acceptance_rationale_dossier,
    list_flagship_acceptance_sheets,
)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _write_json(path: Path, payload: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload + "\n", encoding="utf-8")
    return str(path.relative_to(_repo_root()))


def _refresh_acceptance_assets() -> tuple[str, ...]:
    repo_root = _repo_root()
    written: list[str] = []
    for sheet in list_flagship_acceptance_sheets():
        written.append(
            _write_json(repo_root / sheet.artifact_path, sheet.to_stable_json())
        )
    dashboard = build_flagship_acceptance_dashboard()
    written.append(
        _write_json(repo_root / dashboard.artifact_path, dashboard.to_stable_json())
    )
    ledger = build_flagship_acceptance_history_ledger()
    written.append(
        _write_json(repo_root / ledger.artifact_path, ledger.to_stable_json())
    )
    dossier = build_flagship_acceptance_rationale_dossier()
    written.append(
        _write_json(repo_root / dossier.artifact_path, dossier.to_stable_json())
    )
    return tuple(written)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bijux-proteomics flagship-acceptance-assets",
        description="Refresh published flagship acceptance sheets.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "refresh", help="rewrite published flagship acceptance sheets"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command != "refresh":
        parser.error(f"unsupported command: {args.command}")
        raise AssertionError("parser.error should terminate execution")
    for path in _refresh_acceptance_assets():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
