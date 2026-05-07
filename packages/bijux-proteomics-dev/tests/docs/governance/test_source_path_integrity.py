from __future__ import annotations

from bijux_proteomics_dev.docs.governance.source_path_integrity import (
    collect_source_path_references,
    validate_source_path_references,
)


def test_source_path_integrity_finds_live_repository_source_references() -> None:
    references = collect_source_path_references()

    assert references
    assert any(
        reference.referenced_path == "src/bijux_proteomics_dev/governance/contracts"
        for reference in references
    )


def test_source_path_integrity_rejects_stale_markdown_source_paths() -> None:
    assert validate_source_path_references() == ()
