# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility facade for the canonical PTM review owner."""

from __future__ import annotations

from bijux_proteomics.ptm.cards.review import *  # noqa: F401,F403
from bijux_proteomics.ptm.cards.review import (
    build_ptm_cooccurrence_caution_report as build_ptm_cooccurrence_caution_report,
)
from bijux_proteomics.ptm.cards.review import (
    build_ptm_lab_validation_packet as build_ptm_lab_validation_packet,
)
from bijux_proteomics.ptm.quant.occupancy_estimation import (
    build_ptm_occupancy_counterpart_report as build_ptm_occupancy_counterpart_report,
)
from bijux_proteomics.ptm.regulation.motif_analysis import (
    build_ptm_motif_enrichment_background_provenance_report as build_ptm_motif_enrichment_background_provenance_report,
)

__all__ = [
    *globals().get("__all__", []),
    "build_ptm_cooccurrence_caution_report",
    "build_ptm_lab_validation_packet",
    "build_ptm_motif_enrichment_background_provenance_report",
    "build_ptm_occupancy_counterpart_report",
]
