# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Biological metrics derived from sequences and structures."""

from __future__ import annotations

from agentic_proteins.domain.sequence import primary_summary_from_sequence
from agentic_proteins.domain.structure import (
    gdt_ha,
    gdt_ts,
    kabsch_and_pairs,
    load_structure_from_pdb_text,
    per_residue_plddt_ss,
    residue_count,
    secondary_summary_from_structure,
    tertiary_summary_from_structure,
    tm_score,
)
from agentic_proteins.report import Metrics, SecondarySummary, TertiarySummary


def compute_metrics(
    sequence: str, pdb_text: str, ref_pdb_text: str | None = None
) -> Metrics:
    """Computes full metrics from sequence, predicted PDB, and optional reference."""
    structure = load_structure_from_pdb_text(pdb_text)
    primary = primary_summary_from_sequence(sequence)
    plddts, sss, _aas = per_residue_plddt_ss(structure)
    secondary = secondary_summary_from_structure(structure)
    tertiary = tertiary_summary_from_structure(structure, plddts)
    ref_residues = None
    n_matched_pairs = None
    seq_identity = None
    gap_fraction = None
    if ref_pdb_text:
        ref_structure = load_structure_from_pdb_text(ref_pdb_text)
        ref_residues = residue_count(ref_structure)
        rmsd, n_pairs, ref_arr, pred_arr, seq_id, gap_frac = kabsch_and_pairs(
            pdb_text, ref_pdb_text
        )
        gdt_ts_val = gdt_ts(ref_arr, pred_arr)
        gdt_ha_val = gdt_ha(ref_arr, pred_arr)
        tm_score_val = tm_score(ref_arr, pred_arr, ref_residues)
        _, ref_sss, _ = per_residue_plddt_ss(ref_structure)
        if len(sss) == len(ref_sss):
            q3 = (
                100 * sum(p == r for p, r in zip(sss, ref_sss, strict=False)) / len(sss)
            )
        else:
            q3 = None
        secondary = SecondarySummary(
            pct_helix=secondary.pct_helix,
            pct_sheet=secondary.pct_sheet,
            pct_coil=secondary.pct_coil,
            ss8_pct=secondary.ss8_pct,
            q3=q3,
            q8=None,
            sov99=None,
        )
        tertiary = TertiarySummary(
            mean_plddt=tertiary.mean_plddt,
            plddt_bands=tertiary.plddt_bands,
            pae_median=tertiary.pae_median,
            pae_q90=tertiary.pae_q90,
            rg=tertiary.rg,
            sasa=tertiary.sasa,
            hbonds=tertiary.hbonds,
            rama_outliers_pct=tertiary.rama_outliers_pct,
            clashscore=tertiary.clashscore,
            rmsd=rmsd,
            gdt_ts=gdt_ts_val,
            gdt_ha=gdt_ha_val,
            tm_score=tm_score_val,
            lddt=None,
            n_interfaces=tertiary.n_interfaces,
            buried_sasa=tertiary.buried_sasa,
            irmsd=tertiary.irmsd,
            dockq=tertiary.dockq,
        )
        n_matched_pairs = n_pairs
        seq_identity = seq_id
        gap_fraction = gap_frac
    return Metrics(
        primary,
        secondary,
        tertiary,
        ref_residues,
        n_matched_pairs,
        seq_identity,
        gap_fraction,
    )
