"""License asset synchronization coverage."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(
    0,
    str(
        next(
            parent
            for parent in Path(__file__).resolve().parents
            if parent.name == "bijux-proteomics-dev"
        )
        / "src"
    ),
)

from bijux_proteomics_dev.release.licensing.license_assets import (
    ROOT_LEGAL_ARTIFACTS,
    managed_assets,
    synchronize_license_assets,
)


def test_managed_assets_cover_every_workspace_package() -> None:
    package_targets = {asset.target.parent.name for asset in managed_assets()}
    assert package_targets == {
        "agentic-proteins",
        "bijux-proteomics",
        "bijux-proteomics-core",
        "bijux-proteomics-dev",
        "bijux-proteomics-foundation",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
        "proteomics",
        "proteomics-core",
        "proteomics-foundation",
        "proteomics-intelligence",
        "proteomics-knowledge",
        "proteomics-lab",
        "proteomics-runtime",
    }


def test_license_assets_link_back_to_repository_root() -> None:
    failures: list[str] = []

    for asset in managed_assets():
        if not asset.target.is_symlink():
            failures.append(f"{asset.target}: expected symlink")
            continue
        expected = ROOT_LEGAL_ARTIFACTS[asset.target.name]
        target = asset.target.readlink()
        if target != expected:
            failures.append(f"{asset.target}: {target!s} != {expected!s}")

    assert not failures, "managed legal asset linkage failed:\n" + "\n".join(failures)


def test_license_assets_are_synchronized() -> None:
    assert synchronize_license_assets(check=True) == []
