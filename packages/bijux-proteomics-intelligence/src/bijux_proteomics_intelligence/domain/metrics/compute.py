# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Biological metrics derived from sequences and structures."""

from __future__ import annotations

from bijux_proteomics.domain.sequence import primary_summary_from_sequence
from bijux_proteomics.domain.structure import (
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
from bijux_proteomics_intelligence.report import (
    SS8,
    Metrics,
    Percentage,
    PLDDTBand,
    PrimarySummary,
    Probability,
    SecondarySummary,
    TertiarySummary,
)


def compute_metrics(
    sequence: str, pdb_text: str, ref_pdb_text: str | None = None
) -> Metrics:
    """Computes full metrics from sequence, predicted PDB, and optional reference."""
    structure = load_structure_from_pdb_text(pdb_text)
    core_primary = primary_summary_from_sequence(sequence)
    primary = PrimarySummary(
        length=core_primary.length,
        aa_composition=core_primary.aa_composition,
        gravy=core_primary.gravy,
        isoelectric_point=core_primary.isoelectric_point,
        pct_disorder=core_primary.pct_disorder,
        pct_low_complexity=core_primary.pct_low_complexity,
        has_signal_peptide=core_primary.has_signal_peptide,
        has_tm_segments=core_primary.has_tm_segments,
    )
    plddts, sss, _aas = per_residue_plddt_ss(structure)
    core_secondary = secondary_summary_from_structure(structure)
    secondary = SecondarySummary(
        pct_helix=Percentage(core_secondary.pct_helix),
        pct_sheet=Percentage(core_secondary.pct_sheet),
        pct_coil=Percentage(core_secondary.pct_coil),
        ss8_pct={
            SS8(label): Percentage(value)
            for label, value in core_secondary.ss8_pct.items()
            if label in SS8._value2member_map_
        },
    )
    core_tertiary = tertiary_summary_from_structure(structure, plddts)
    tertiary = TertiarySummary(
        mean_plddt=(
            float(core_tertiary.mean_plddt)
            if core_tertiary.mean_plddt is not None
            else float("nan")
        ),
        plddt_bands={
            PLDDTBand(label): Percentage(value)
            for label, value in core_tertiary.plddt_bands.items()
            if label in PLDDTBand._value2member_map_
        },
        pae_median=core_tertiary.pae_median,
        pae_q90=core_tertiary.pae_q90,
        rg=core_tertiary.rg,
        sasa=core_tertiary.sasa,
        hbonds=core_tertiary.hbonds,
        rama_outliers_pct=core_tertiary.rama_outliers_pct,
        clashscore=core_tertiary.clashscore,
        rmsd=core_tertiary.rmsd,
        gdt_ts=core_tertiary.gdt_ts,
        gdt_ha=core_tertiary.gdt_ha,
        tm_score=core_tertiary.tm_score,
        lddt=core_tertiary.lddt,
        n_interfaces=core_tertiary.n_interfaces,
        buried_sasa=core_tertiary.buried_sasa,
        irmsd=core_tertiary.irmsd,
        dockq=core_tertiary.dockq,
    )
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
            q3_value = (
                100 * sum(p == r for p, r in zip(sss, ref_sss, strict=False)) / len(sss)
            )
        else:
            q3_value = None
        secondary = SecondarySummary(
            pct_helix=secondary.pct_helix,
            pct_sheet=secondary.pct_sheet,
            pct_coil=secondary.pct_coil,
            ss8_pct=secondary.ss8_pct,
            q3=Percentage(q3_value) if q3_value is not None else None,
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
        seq_identity = Probability(seq_id)
        gap_fraction = Probability(gap_frac)
    return Metrics(
        primary,
        secondary,
        tertiary,
        ref_residues,
        n_matched_pairs,
        seq_identity,
        gap_fraction,
    )
