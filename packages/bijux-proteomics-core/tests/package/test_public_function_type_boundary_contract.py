# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.ptm import (
    build_ptm_motif_windows,
    map_ptm_evidence_to_protein_sites,
)
from bijux_proteomics.ptm.benchmarks import (
    build_ptm_family_credibility_track_report,
)
from bijux_proteomics.ptm.review import (
    build_phospho_specific_review_fixture_report,
)
from bijux_proteomics_foundation.testing.public_function_type_boundaries import (
    build_public_function_type_boundary_report,
)


def test_core_ptm_public_functions_avoid_free_dict_boundaries() -> None:
    report = build_public_function_type_boundary_report(
        (
            build_ptm_motif_windows,
            map_ptm_evidence_to_protein_sites,
            build_ptm_family_credibility_track_report,
            build_phospho_specific_review_fixture_report,
        )
    )

    assert report.function_count == 4
    assert report.violating_observations == ()
