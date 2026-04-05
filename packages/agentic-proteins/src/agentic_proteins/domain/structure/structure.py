# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Structure-level utilities and metrics."""

from __future__ import annotations

import io
import os
import shutil
import tempfile

from Bio.Align import PairwiseAligner
from Bio.Align.substitution_matrices import load as load_subst
from Bio.PDB import DSSP, PDBIO, PDBParser, Polypeptide, Structure, Superimposer
from Bio.SeqUtils import seq1
from loguru import logger
import numpy as np

from agentic_proteins.report import SecondarySummary, TertiarySummary

_RES3_CUSTOM = {
    "MSE": "M",  # selenomethionine → Met
    "SEC": "U",  # selenocysteine
    "PYL": "O",  # pyrrolysine
    "UNK": "X",
}


def _res3_to1(resname: str) -> str:
    """Convert a 3-letter residue to 1-letter; return 'X' on failure."""
    name = (resname or "").strip().upper()
    try:
        return seq1(name, custom_map=_RES3_CUSTOM)
    except Exception:
        return "X"


def load_structure_from_pdb_text(pdb_text: str) -> Structure:
    """Loads a protein structure from PDB text."""
    parser = PDBParser(QUIET=True)
    handle = io.StringIO(pdb_text)
    return parser.get_structure("pred", handle)


def residue_count(structure: Structure) -> int:
    """Counts the number of amino acid residues in the structure.

    Args:
        structure: The Bio.PDB Structure object.

    Returns:
        The count of standard amino acid residues.
    """
    return sum(
        1 for r in structure.get_residues() if Polypeptide.is_aa(r, standard=True)
    )


def mean_plddt_from_ca_bfactor(structure: Structure) -> float:
    """Computes the mean pLDDT from CA B-factors.

    Args:
        structure: The Bio.PDB Structure object.

    Returns:
        The mean pLDDT value, or NaN if no B-factors found.
    """
    b = []
    for res in structure.get_residues():
        if Polypeptide.is_aa(res, standard=True) and res.has_id("CA"):
            ca = res["CA"]
            bf = ca.get_bfactor()
            if bf is not None:
                b.append(float(bf))
    return float(np.mean(b)) if b else float("nan")


def per_residue_plddt_ss(
    structure: Structure,
) -> tuple[list[float], list[str], list[str]]:
    """Extracts per-residue pLDDT, secondary structure, and amino acids.

    Args:
        structure: The Bio.PDB Structure object.

    Returns:
        Tuple of (plddts, secondary structures, amino acids).
    """
    residues = [
        r for r in structure.get_residues() if Polypeptide.is_aa(r, standard=True)
    ]

    residues = [r for r in residues if getattr(r, "id", ("",))[0] == " "]
    aas = [_res3_to1(r.get_resname()) for r in residues]

    plddts = []
    for r in residues:
        if r.has_id("CA"):
            ca = r["CA"]
            plddt = ca.get_bfactor()
            plddts.append(float(plddt) if plddt is not None else 0.0)
        else:
            plddts.append(0.0)

    # Default coil
    sss = ["C"] * len(residues)

    try:
        if shutil.which("mkdssp") is None:
            raise RuntimeError("mkdssp not found on PATH")
        with tempfile.TemporaryDirectory() as tmpd:
            p = os.path.join(tmpd, "model.pdb")
            io_writer = PDBIO()
            io_writer.set_structure(structure)
            io_writer.save(p)
            model = structure[0]
            dssp = DSSP(model, p, dssp="mkdssp")

            ss_map = {}
            for (chain_id, res_id), props in dssp.property_dict.items():
                hetflag, resseq, icode = res_id
                if hetflag == " ":
                    ss = props.get("SS") or "C"  # '', None → "C"
                    ss_map[(chain_id, resseq, (icode or " ").strip())] = ss

            idx = 0
            for ch in model:
                for r in ch:
                    if Polypeptide.is_aa(r, standard=True):
                        key = (ch.id, r.id[1], (r.id[2] or " ").strip())
                        sss[idx] = ss_map.get(key, "C")
                        idx += 1
    except Exception as e:
        logger.warning("DSSP failed ({}); using coil SS", e)

    return plddts, sss, aas


def secondary_summary_from_structure(structure: Structure) -> SecondarySummary:
    """Computes secondary structure summary from the structure.

    Args:
        structure: The Bio.PDB Structure object.

    Returns:
        SecondarySummary object.
    """
    plddts, sss, _ = per_residue_plddt_ss(structure)
    n = len(sss)
    if n == 0:
        return SecondarySummary()
    ss8_counts = {}
    helix = sheet = coil = 0
    for s in sss:
        ss8_counts[s] = ss8_counts.get(s, 0) + 1
        if s in "HGI":
            helix += 1
        elif s in "EB":
            sheet += 1
        else:
            coil += 1
    ss8_pct = {k: 100.0 * v / n for k, v in ss8_counts.items()}
    return SecondarySummary(
        pct_helix=100.0 * helix / n,
        pct_sheet=100.0 * sheet / n,
        pct_coil=100.0 * coil / n,
        ss8_pct=ss8_pct,
    )


def tertiary_summary_from_structure(
    structure: Structure, plddts: list[float]
) -> TertiarySummary:
    """Computes tertiary structure summary from the structure and pLDDTs.

    Args:
        structure: The Bio.PDB Structure object.
        plddts: List of per-residue pLDDT values.

    Returns:
        TertiarySummary object.
    """
    mean_plddt = np.mean(plddts)
    # Bands
    bands = {"≥90": 0, "70–90": 0, "50–70": 0, "<50": 0}
    for p in plddts:
        if p >= 90:
            bands["≥90"] += 1
        elif p >= 70:
            bands["70–90"] += 1
        elif p >= 50:
            bands["50–70"] += 1
        else:
            bands["<50"] += 1
    n = len(plddts)
    plddt_bands = {k: 100.0 * v / n if n else 0.0 for k, v in bands.items()}
    # Placeholders for other fields; would require tools like FreeSASA, MolProbity, etc.
    pae_median = None
    pae_q90 = None
    rg = None
    sasa = None
    hbonds = None
    rama_outliers_pct = None
    clashscore = None
    n_interfaces = None
    buried_sasa = None
    irmsd = None
    dockq = None
    return TertiarySummary(
        mean_plddt=mean_plddt,
        plddt_bands=plddt_bands,
        pae_median=pae_median,
        pae_q90=pae_q90,
        rg=rg,
        sasa=sasa,
        hbonds=hbonds,
        rama_outliers_pct=rama_outliers_pct,
        clashscore=clashscore,
        rmsd=None,  # From alignment
        gdt_ts=None,
        gdt_ha=None,
        tm_score=None,
        lddt=None,
        n_interfaces=n_interfaces,
        buried_sasa=buried_sasa,
        irmsd=irmsd,
        dockq=dockq,
    )


def get_protein_chain(
    structure: Structure, chain_id: str | None = None
) -> Structure.Child:
    """Selects a protein chain from the structure.

    Args:
        structure: The Bio.PDB Structure object.
        chain_id: Optional chain ID to select.

    Returns:
        The selected chain.

    Raises:
        ValueError: If chain not found or no protein chain.
    """
    model = structure[0]
    if chain_id:
        if chain_id in model:
            return model[chain_id]
        raise ValueError(f"Chain {chain_id} not found")
    for chain in model:
        if any(Polypeptide.is_aa(res, standard=True) for res in chain):
            return chain
    raise ValueError("No protein chain found")


def best_ca(res):
    """Selects the best CA atom from a residue based on occupancy and altloc.

    Args:
        res: The Bio.PDB Residue object.

    Returns:
        The best CA atom or None.
    """
    atoms = [a for a in res.get_unpacked_list() if a.id == "CA"]
    if not atoms:
        return None
    atoms.sort(key=lambda a: (a.get_occupancy() or 0.0, a.altloc == "A"), reverse=True)
    return atoms[0]


def kabsch_and_pairs(
    pdb_pred_text: str,
    pdb_ref_text: str,
    pred_chain: str | None = None,
    ref_chain: str | None = None,
) -> tuple[float, int, np.ndarray, np.ndarray, float, float]:
    """Performs Kabsch superposition and computes alignment metrics.

    Args:
        pdb_pred_text: Predicted PDB text.
        pdb_ref_text: Reference PDB text.
        pred_chain: Optional predicted chain ID.
        ref_chain: Optional reference chain ID.

    Returns:
        Tuple of (RMSD, num_pairs, ref_coords, pred_coords, seq_id, gap_frac).

    Raises:
        ValueError: On alignment failure or insufficient pairs.
    """
    parser = PDBParser(QUIET=True)
    s_pred = parser.get_structure("pred", io.StringIO(pdb_pred_text))
    s_ref = parser.get_structure("ref", io.StringIO(pdb_ref_text))
    chain_pred = get_protein_chain(s_pred, pred_chain)
    chain_ref = get_protein_chain(s_ref, ref_chain)
    pred_residues = [r for r in chain_pred if Polypeptide.is_aa(r, standard=True)]
    ref_residues = [r for r in chain_ref if Polypeptide.is_aa(r, standard=True)]
    seq_pred = "".join(seq1(r.get_resname()) for r in pred_residues)
    seq_ref = "".join(seq1(r.get_resname()) for r in ref_residues)
    # Local alignment for flexible proteins
    aligner = PairwiseAligner()
    aligner.mode = "local"
    aligner.substitution_matrix = load_subst("BLOSUM62")
    aligner.open_gap_score = -8.0
    aligner.extend_gap_score = -0.2
    aligner.target_internal_open_gap_score = -8.0
    aligner.query_internal_open_gap_score = -8.0
    alignments = aligner.align(seq_pred, seq_ref)
    if not alignments:
        raise ValueError("No alignment possible")
    alignment = alignments[0]
    pred_aln, ref_aln = alignment[0], alignment[1]
    cols = list(zip(pred_aln, ref_aln, strict=False))
    cols_both = [(p, r) for (p, r) in cols if p != "-" and r != "-"]
    matches = sum(p == r for p, r in cols_both)
    seq_id = matches / len(cols_both) if cols_both else 0.0
    gap_frac = sum(p == "-" or r == "-" for p, r in cols) / len(cols) if cols else 0.0
    # Robust pairing
    ca_pairs = []
    p_idx, r_idx = 0, 0
    for p, r in cols:
        if p != "-" and r != "-":
            if p_idx < len(pred_residues) and r_idx < len(ref_residues):
                pred_res = pred_residues[p_idx]
                ref_res = ref_residues[r_idx]
                ca_p = best_ca(pred_res)
                ca_r = best_ca(ref_res)
                if ca_p and ca_r:
                    ca_pairs.append((ca_r, ca_p))
            p_idx += 1
            r_idx += 1
        elif p != "-":
            p_idx += 1
        elif r != "-":
            r_idx += 1
    n_pairs = len(ca_pairs)
    if n_pairs < 3:
        raise ValueError(f"Insufficient CA pairs: {n_pairs}")
    # Superimpose
    sup = Superimposer()
    ref_atoms = [a for a, _ in ca_pairs]
    pred_atoms = [a for _, a in ca_pairs]
    sup.set_atoms(ref_atoms, pred_atoms)
    rmsd = sup.rms
    # Coords: Original for ref, transformed for pred (no extra centering—Superimposer handles it)
    ref_arr = np.array([a.get_coord() for a, _ in ca_pairs])
    pred_arr_orig = np.array([a.get_coord() for _, a in ca_pairs])
    rotation = sup.rotran[0]
    translation = sup.rotran[1]
    pred_arr_aligned = np.dot(pred_arr_orig, rotation) + translation
    return rmsd, n_pairs, ref_arr, pred_arr_aligned, seq_id, gap_frac


def _pairwise_dist(p_coords: np.ndarray, q_coords: np.ndarray) -> np.ndarray:
    """Computes pairwise Euclidean distances between coordinate arrays."""
    return np.linalg.norm(p_coords - q_coords, axis=1)


def gdt_ts(ref_coords: np.ndarray, pred_coords: np.ndarray) -> float:
    """Computes GDT-TS score (thresholds 1,2,4,8 Å)."""
    if ref_coords.shape != pred_coords.shape:
        raise ValueError("Coordinate arrays must have the same shape.")
    d = _pairwise_dist(ref_coords, pred_coords)
    n_total = len(d)
    if n_total == 0:
        return 0.0
    fractions = [(d <= t).sum() / n_total for t in (1.0, 2.0, 4.0, 8.0)]
    return 100.0 * np.mean(fractions)


def gdt_ha(ref_coords: np.ndarray, pred_coords: np.ndarray) -> float:
    """Computes GDT-HA score (thresholds 0.5,1,2,4 Å)."""
    d = _pairwise_dist(ref_coords, pred_coords)
    n_total = len(d)
    if n_total == 0:
        return 0.0
    fractions = [(d <= t).sum() / n_total for t in (0.5, 1.0, 2.0, 4.0)]
    return 100.0 * np.mean(fractions)


def tm_score(
    ref_coords: np.ndarray, pred_coords: np.ndarray, l_ref: int | None = None
) -> float:
    """Computes TM-score."""
    if ref_coords.shape != pred_coords.shape:
        raise ValueError("Coordinate arrays must have the same shape.")
    d = _pairwise_dist(ref_coords, pred_coords)
    l_total = l_ref or len(d)
    if l_total == 0:
        return 0.0
    d0 = 1.24 * (l_total - 15) ** (1 / 3) - 1.8
    d0 = max(d0, 0.5)
    return float(np.mean(1.0 / (1.0 + (d / d0) ** 2)))
