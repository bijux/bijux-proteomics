# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Materialize checked challenge-corpus assets for flagship holdouts and perturbations."""

from __future__ import annotations

import argparse
from pathlib import Path

from bijux_proteomics.benchmarks.flagship_challenge_corpora import (
    ChallengeKind,
    build_blinded_holdout_reports,
    build_flagship_challenge_registry,
    flagship_challenge_registry_path,
)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _write_text(repo_relative_path: str, content: str) -> None:
    path = _repo_root() / repo_relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(repo_relative_path: str, payload: object) -> None:
    import json

    _write_text(repo_relative_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _holdout_readme(report) -> str:
    return "\n".join(
        (
            f"# {report.workflow_family.upper()} Blinded Holdout",
            "",
            "This challenge root freezes the main package and review surfaces first, then reveals",
            "whether the withheld family-transfer findings still support the same workflow claims.",
            "",
            f"- challenge id: `{report.challenge_id}`",
            f"- primary package id: `{report.primary_package_id}`",
            f"- holdout package id: `{report.holdout_package_id}`",
            f"- revealed report: `{report.artifact_path}`",
        )
    ) + "\n"


def refresh_flagship_challenge_assets() -> tuple[str, ...]:
    """Write checked blinded holdout assets to the product-owned challenge root."""

    written: list[str] = []
    for report in build_blinded_holdout_reports():
        challenge_root = next(
            entry.challenge_root
            for entry in build_flagship_challenge_registry().entries
            if entry.challenge_id == report.challenge_id
        )
        manifest_path = f"{challenge_root}/challenge_manifest.json"
        readme_path = f"{challenge_root}/README.md"
        _write_json(
            manifest_path,
            {
                "challenge_id": report.challenge_id,
                "challenge_kind": ChallengeKind.BLINDED_HOLDOUT.value,
                "workflow_family": report.workflow_family,
                "primary_package_id": report.primary_package_id,
                "holdout_package_id": report.holdout_package_id,
                "frozen_surface_paths": list(report.frozen_surface_paths),
                "revealed_report_path": report.artifact_path,
                "note": report.note,
            },
        )
        _write_json(report.artifact_path, report.model_dump(mode="json"))
        _write_text(readme_path, _holdout_readme(report))
        written.extend((manifest_path, report.artifact_path, readme_path))
    registry = build_flagship_challenge_registry()
    _write_json(flagship_challenge_registry_path(), registry.model_dump(mode="json"))
    written.append(flagship_challenge_registry_path())
    return tuple(written)


def main(argv: list[str] | None = None) -> int:
    """Refresh checked flagship challenge assets."""

    parser = argparse.ArgumentParser(
        description="Materialize flagship blinded holdout and perturbation assets."
    )
    parser.add_argument(
        "command",
        choices=("refresh",),
        help="refresh checked challenge-corpus assets",
    )
    args = parser.parse_args(argv)
    if args.command == "refresh":
        for path in refresh_flagship_challenge_assets():
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
