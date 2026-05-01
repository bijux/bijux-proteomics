# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.external_credibility_iteration20 import (
    AgenticProteinsMigrationItem,
    build_agentic_proteins_migration_report,
)


def test_build_agentic_proteins_migration_report_tracks_blocking_gaps() -> None:
    report = build_agentic_proteins_migration_report(
        "migration-legacy-01",
        (
            AgenticProteinsMigrationItem(
                legacy_surface="agentic.run_dia",
                canonical_surface="bijux workflow-dia-import",
                compatibility_mode="shim-enabled",
            ),
        ),
        blocking_gaps=("missing-cli-flag-parity",),
    )

    assert report.migration_ready is False
    assert report.blocking_gaps == ("missing-cli-flag-parity",)
