# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _workflow(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_publish_workflows_cover_all_release_packages() -> None:
    root = _repo_root()
    workflows = root / ".github" / "workflows"

    expected = {
        "agentic-proteins",
        "bijux-proteomics-foundation",
        "bijux-proteomics-core",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
    }

    found = {
        path.name.removeprefix("publish-").removesuffix(".yml")
        for path in workflows.glob("publish-*.yml")
    }

    assert expected.issubset(found)


def test_publish_workflows_use_package_scoped_builds() -> None:
    root = _repo_root()
    workflows = root / ".github" / "workflows"

    for path in workflows.glob("publish-*.yml"):
        workflow = _workflow(path)
        build_with = _as_dict(
            _as_dict(_as_dict(workflow.get("jobs")).get("build")).get("with")
        )
        package_slug = build_with.get("package_slug")
        assert isinstance(package_slug, str)
        if package_slug == "agentic-proteins":
            package_dir = "packages/agentic-proteins"
        else:
            package_dir = f"packages/{package_slug}"

        assert build_with.get("package_dir") == package_dir
        assert build_with.get("dist_subdir") == f"build/{package_slug}"
