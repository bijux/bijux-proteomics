from __future__ import annotations

from bijux_proteomics_dev.quality.artifacts.repository_file_ownership import (
    REPOSITORY_FILE_OWNERSHIP_PATH,
    build_repository_file_ownership_matrix,
    run,
    validate_repository_file_ownership_matrix,
)


def test_repository_file_ownership_matrix_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_repository_file_ownership_matrix_covers_storage_boundaries() -> None:
    matrix = {area.area_id: area for area in build_repository_file_ownership_matrix()}

    assert REPOSITORY_FILE_OWNERSHIP_PATH.exists()
    assert tuple(matrix) == (
        "root-directories",
        "package-docs",
        "benchmark-assets",
        "generated-outputs",
        "maintainer-automation",
    )
    assert "artifacts" in matrix["generated-outputs"].anchor_paths
    assert any(
        "packages/*" in line
        for line in matrix["generated-outputs"].prohibited_alternates
    )
    assert "make release-preflight" in matrix["maintainer-automation"].cleanup_commands


def test_repository_file_ownership_matrix_has_no_internal_consistency_failures() -> (
    None
):
    assert validate_repository_file_ownership_matrix() == ()
