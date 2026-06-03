from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.artifacts.generated_file_markers import (
    GENERATED_FILE_MARKER_POLICY_PATH,
    GeneratedFileMarkerPolicy,
    GeneratedFileMarkerSurface,
    build_generated_file_marker_violations,
    load_generated_file_marker_policy,
    run,
)
from bijux_proteomics_foundation.testing.generated_file_markers import (
    GeneratedFileMarkerKind,
)


def _policy(*surfaces: GeneratedFileMarkerSurface) -> GeneratedFileMarkerPolicy:
    return GeneratedFileMarkerPolicy(
        name="generated-file-marker-test-policy",
        surfaces=surfaces,
    )


def test_generated_file_marker_policy_manifest_is_repository_owned() -> None:
    assert GENERATED_FILE_MARKER_POLICY_PATH.as_posix().endswith(
        "configs/package-governance/generated-file-marker-surfaces.toml"
    )


def test_generated_file_marker_policy_manifest_covers_governed_generated_families() -> (
    None
):
    policy = load_generated_file_marker_policy()

    assert policy.name == "generated-file-marker-surfaces"
    assert tuple(surface.path_glob for surface in policy.surfaces) == (
        "configs/package-governance/**/*.toml",
        ".github/workflows/*.yml",
        ".github/*.yml",
        ".bijux/shared/bijux-gh/workflows/*.yml",
    )
    config_surface = policy.surfaces[0]
    assert (
        "configs/package-governance/canonical-package-tree-layout.toml"
        in config_surface.excluded_paths
    )
    assert (
        "configs/package-governance/internal-orphan-module-allowlist.toml"
        in config_surface.excluded_paths
    )


def test_generated_file_marker_policy_rejects_missing_marker_headers(
    tmp_path: Path,
) -> None:
    tracked_dir = tmp_path / "configs" / "package-governance"
    tracked_dir.mkdir(parents=True)
    (tracked_dir / "generated-report.toml").write_text(
        "[report]\nname = 'missing-marker'\n",
        encoding="utf-8",
    )

    violations = build_generated_file_marker_violations(
        _policy(
            GeneratedFileMarkerSurface(
                path_glob="configs/package-governance/**/*.toml",
                marker_kind=GeneratedFileMarkerKind.GENERATED_HEADER,
                excluded_paths=(),
            )
        ),
        repo_root=tmp_path,
    )

    assert len(violations) == 1
    assert violations[0].code == "missing-generated-file-marker"


def test_generated_file_marker_policy_allows_excluded_manual_files(
    tmp_path: Path,
) -> None:
    tracked_dir = tmp_path / ".github"
    tracked_dir.mkdir(parents=True)
    (tracked_dir / "dependabot.yml").write_text(
        "version: 2\n",
        encoding="utf-8",
    )

    violations = build_generated_file_marker_violations(
        _policy(
            GeneratedFileMarkerSurface(
                path_glob=".github/*.yml",
                marker_kind=GeneratedFileMarkerKind.SSOT_NOTICE,
                excluded_paths=(".github/dependabot.yml",),
            )
        ),
        repo_root=tmp_path,
    )

    assert violations == ()


def test_live_generated_file_marker_policy_passes() -> None:
    assert build_generated_file_marker_violations() == ()
    assert run(check=True) == 0
