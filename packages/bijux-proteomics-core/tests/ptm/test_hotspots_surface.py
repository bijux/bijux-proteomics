# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.ptm import (
    PtmHotspotSiteResult,
    detect_ptm_hotspots,
    render_ptm_hotspots_tsv,
)


def test_detect_ptm_hotspots_clusters_only_sites_within_threshold() -> None:
    entries = detect_ptm_hotspots(
        (
            PtmHotspotSiteResult(
                site_id="P11111:S5:Phospho",
                protein_id="P11111",
                position=5,
                signed_effect=1.8,
            ),
            PtmHotspotSiteResult(
                site_id="P11111:T8:Phospho",
                protein_id="P11111",
                position=8,
                signed_effect=1.4,
            ),
            PtmHotspotSiteResult(
                site_id="P11111:Y30:Phospho",
                protein_id="P11111",
                position=30,
                signed_effect=1.6,
            ),
            PtmHotspotSiteResult(
                site_id="P11111:S45:Phospho",
                protein_id="P11111",
                position=45,
                signed_effect=-0.9,
            ),
        ),
        protein_length=120,
        max_distance=3,
    )

    assert len(entries) == 1
    hotspot = entries[0]
    assert hotspot.protein_id == "P11111"
    assert hotspot.cluster_start == 5
    assert hotspot.cluster_end == 8
    assert hotspot.site_ids == ("P11111:S5:Phospho", "P11111:T8:Phospho")


def test_detect_ptm_hotspots_scores_direction_consistency_and_renders_surface() -> None:
    entries = detect_ptm_hotspots(
        (
            PtmHotspotSiteResult(
                site_id="P22222:S12:Phospho",
                protein_id="P22222",
                position=12,
                signed_effect=2.0,
            ),
            PtmHotspotSiteResult(
                site_id="P22222:T14:Phospho",
                protein_id="P22222",
                position=14,
                signed_effect=1.7,
            ),
            PtmHotspotSiteResult(
                site_id="P22222:Y15:Phospho",
                protein_id="P22222",
                position=15,
                signed_effect=-0.8,
            ),
        ),
        protein_length={"P22222": 90},
        max_distance=3,
    )
    rendered = render_ptm_hotspots_tsv(entries)

    assert len(entries) == 1
    hotspot = entries[0]
    assert hotspot.direction_consistency == 0.666667
    assert hotspot.hotspot_score > 0.0
    assert rendered.startswith(
        "protein_id\tcluster_start\tcluster_end\tsite_ids\tdirection_consistency\thotspot_score\n"
    )
    assert "P22222\t12\t15\tP22222:S12:Phospho;P22222:T14:Phospho;P22222:Y15:Phospho\t0.666667\t" in rendered
