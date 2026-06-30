# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Commands that refresh and audit flagship benchmark asset roots."""

from __future__ import annotations

import argparse
from pathlib import Path

from bijux_proteomics.benchmarks.flagship.dda_reviewable_package import (
    build_dda_reviewable_package,
)
from bijux_proteomics.benchmarks.flagship.asset_roots import (
    build_flagship_asset_root_contract,
    write_flagship_asset_support_files,
)
from bijux_proteomics.benchmarks.flagship.public_packages import (
    build_flagship_public_package_artifact_inventories,
    build_flagship_public_package_lifecycle_records,
    build_flagship_public_package_quality_sheets,
    list_flagship_public_benchmark_packages,
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


def _materialize_generated_package_files() -> tuple[str, ...]:
    repo_root = _repo_root()
    contract = build_flagship_asset_root_contract()
    inventories = {
        inventory.package_id: inventory
        for inventory in build_flagship_public_package_artifact_inventories()
    }
    quality_sheets = {
        sheet.package_id: sheet
        for sheet in build_flagship_public_package_quality_sheets()
    }
    lifecycle_records = {
        record.package_id: record
        for record in build_flagship_public_package_lifecycle_records()
    }
    package_map = {
        package.package_id: package
        for package in list_flagship_public_benchmark_packages()
    }
    written: list[str] = []
    dda_package = build_dda_reviewable_package()
    for entry in contract.entries:
        if entry.workflow_family == "dda":
            written.append(
                _write_json(
                    repo_root / f"{dda_package.package_root}/package_manifest.json",
                    dda_package.to_stable_json(),
                )
            )
            written.append(
                _write_json(
                    repo_root / f"{dda_package.package_root}/artifact_inventory.json",
                    JsonListPayload.from_models(dda_package.artifacts).to_stable_json(),
                )
            )
            written.append(
                _write_json(
                    repo_root
                    / f"{dda_package.package_root}/scientific_invariants.json",
                    JsonListPayload.from_models(
                        dda_package.scientific_invariants
                    ).to_stable_json(),
                )
            )
            written.append(
                _write_json(
                    repo_root
                    / f"{dda_package.package_root}/warning_demonstrations.json",
                    JsonListPayload.from_models(
                        dda_package.warning_demonstrations
                    ).to_stable_json(),
                )
            )
        else:
            package = package_map[entry.package_id]
            inventory = inventories[entry.package_id]
            written.append(
                _write_json(
                    repo_root / package.benchmark_manifest_path,
                    package.to_stable_json(),
                )
            )
            written.append(
                _write_json(
                    repo_root / package.artifact_inventory_path,
                    inventory.to_stable_json(),
                )
            )
        quality_sheet = quality_sheets[entry.package_id]
        lifecycle_record = lifecycle_records[entry.package_id]
        written.append(
            _write_json(
                repo_root / quality_sheet.quality_path,
                quality_sheet.to_stable_json(),
            )
        )
        written.append(
            _write_json(
                repo_root / lifecycle_record.lifecycle_path,
                lifecycle_record.to_stable_json(),
            )
        )
    return tuple(written)


class JsonListPayload:
    """Stable wrapper for list-shaped generated JSON payloads."""

    def __init__(self, items: tuple[dict[str, object], ...]) -> None:
        self._items = items

    @classmethod
    def from_models(cls, models: tuple[object, ...]) -> JsonListPayload:
        return cls(
            tuple(
                model.model_dump(mode="json")  # type: ignore[attr-defined]
                for model in models
            )
        )

    def to_stable_json(self) -> str:
        import json

        return json.dumps(self._items, indent=2, sort_keys=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bijux-proteomics flagship-asset-maintenance",
        description=(
            "Refresh governed support files for flagship public benchmark asset roots."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh = subparsers.add_parser(
        "refresh",
        help="rewrite shared asset-root contract, freshness report, obsolescence audit, and per-package support files",
    )
    refresh.add_argument(
        "--check-remote",
        action="store_true",
        help="probe public reference URLs instead of writing a local-only freshness report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "refresh":
        written = list(
            write_flagship_asset_support_files(check_remote=args.check_remote)
        )
        written.extend(_materialize_generated_package_files())
        for path in written:
            print(path)
        return 0
    parser.error(f"unsupported command: {args.command}")
    raise AssertionError("parser.error should terminate execution")


if __name__ == "__main__":
    raise SystemExit(main())
