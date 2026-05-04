# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration import (
    ArchiveRetentionPackageInput,
    build_archive_retention_package,
)


def test_build_archive_retention_package_normalizes_references() -> None:
    package = build_archive_retention_package(
        ArchiveRetentionPackageInput(
            package_id="archive-1",
            schema_refs=("schema.a", "schema.a", "schema.b"),
            artifact_paths=("artifacts/b.json", "artifacts/a.json"),
            evidence_pointer_ids=("ev-2", "ev-1"),
            compatibility_metadata=("python=3.12",),
            caveats=("synthetic-corpus",),
        )
    )

    assert package.schema_refs == ("schema.a", "schema.b")
    assert package.artifact_paths[0] == "artifacts/a.json"
