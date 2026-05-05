"""Compatibility forwarding module for canonical core and intelligence domain ownership."""

from bijux_proteomics.domain.sequence import HYDROPATHY, PKA_C_TERM, PKA_N_TERM, PKA_SIDE
from bijux_proteomics.domain.sequence.summary import primary_summary_from_sequence
from bijux_proteomics.domain.structure import (
    _res3_to1,
    best_ca,
    gdt_ha,
    gdt_ts,
    get_protein_chain,
    kabsch_and_pairs,
    load_structure_from_pdb_text,
    mean_plddt_from_ca_bfactor,
    per_residue_plddt_ss,
    residue_count,
    secondary_summary_from_structure,
    tertiary_summary_from_structure,
    tm_score,
)
from bijux_proteomics_intelligence.domain.metrics.compute import compute_metrics
from bijux_proteomics_intelligence.domain.structure.confidence import (
    low_confidence_segments,
)

__all__ = [
    "HYDROPATHY",
    "PKA_C_TERM",
    "PKA_N_TERM",
    "PKA_SIDE",
    "_res3_to1",
    "best_ca",
    "compute_metrics",
    "gdt_ha",
    "gdt_ts",
    "get_protein_chain",
    "kabsch_and_pairs",
    "load_structure_from_pdb_text",
    "low_confidence_segments",
    "mean_plddt_from_ca_bfactor",
    "per_residue_plddt_ss",
    "primary_summary_from_sequence",
    "residue_count",
    "secondary_summary_from_structure",
    "tertiary_summary_from_structure",
    "tm_score",
]
