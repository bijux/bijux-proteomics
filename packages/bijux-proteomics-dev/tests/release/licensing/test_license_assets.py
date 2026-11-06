"""License asset synchronization coverage."""

from __future__ import annotations

from pathlib import Path
import sys

from pytest import MonkeyPatch

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

from bijux_proteomics_dev.release.licensing import license_assets
from bijux_proteomics_dev.release.licensing.license_assets import (
    ManagedAsset,
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


def test_license_assets_are_self_contained_and_match_repository_root() -> None:
    for asset in managed_assets():
        assert not asset.target.is_symlink(), str(asset.target)
        assert asset.target.read_bytes() == asset.source.read_bytes()


def test_license_assets_are_synchronized() -> None:
    assert synchronize_license_assets(check=True) == []


def test_synchronization_replaces_archive_escaping_symlinks(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    source = tmp_path / "LICENSE"
    source.write_bytes(b"canonical legal content\n")
    target = tmp_path / "packages" / "example" / "LICENSE"
    target.parent.mkdir(parents=True)
    target.symlink_to("../../LICENSE")
    monkeypatch.setattr(
        license_assets, "managed_assets", lambda: (ManagedAsset(source, target),)
    )

    assert synchronize_license_assets(check=True) == [target]
    assert target.is_symlink()
    assert synchronize_license_assets() == [target]
    assert not target.is_symlink()
    assert target.read_bytes() == source.read_bytes()
    assert synchronize_license_assets(check=True) == []

    source.write_bytes(b"revised canonical legal content\n")
    assert synchronize_license_assets(check=True) == [target]
    assert synchronize_license_assets() == [target]
    assert target.read_bytes() == source.read_bytes()
