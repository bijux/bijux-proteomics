# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import math
import textwrap
from typing import Tuple

import numpy as np
import pytest

import agentic_proteins.domain as U
from agentic_proteins.domain.structure import structure as structure_mod


# ------------------------ tiny PDB builders ------------------------

def _pdb_n_residues(
    n: int,
    chain_id: str = "A",
    start_serial: int = 1,
    start_resseq: int = 1,
    bfactor: float = 80.0,
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> str:
    """
    Build a minimal PDB with `n` ALA residues, single CA atom per residue.
    Coordinates laid on a simple grid; B-factor constant.
    """
    ox, oy, oz = offset
    lines = []
    serial = start_serial
    for i in range(n):
        x = ox + float(i % 5)
        y = oy + float(i // 5)
        z = oz
        resseq = start_resseq + i
        lines.append(
            f"ATOM  {serial:5d}  CA  ALA {chain_id}{resseq:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00{bfactor:6.2f}           C"
        )
        serial += 1
    lines.append("TER")
    lines.append("END")
    return "\n".join(lines) + "\n"


def _pdb_three_residues(
    chain_id: str = "A",
    b1: float = 90.0,
    b2_a: float = 80.0,
    b2_b: float | None = None,  # altloc B for CA at res 2
    b3: float = 70.0,
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> str:
    ox, oy, oz = offset
    lines = []
    # res 1
    lines.append(
        f"ATOM      1  CA  ALA {chain_id}   1    {0.0+ox:8.3f}{0.0+oy:8.3f}{0.0+oz:8.3f}  1.00{b1:6.2f}           C"
    )
    # res 2 (altloc A)
    lines.append(
        f"ATOM      2  CA AALA {chain_id}   2    {1.0+ox:8.3f}{0.0+oy:8.3f}{0.0+oz:8.3f}  0.50{b2_a:6.2f}           C"
    )
    # res 2 (altloc B)
    if b2_b is not None:
        lines.append(
            f"ATOM      3  CA BALA {chain_id}   2    {1.2+ox:8.3f}{0.0+oy:8.3f}{0.0+oz:8.3f}  0.80{b2_b:6.2f}           C"
        )
    # res 3
    lines.append(
        f"ATOM      4  CA  ALA {chain_id}   3    {0.0+ox:8.3f}{1.0+oy:8.3f}{0.0+oz:8.3f}  1.00{b3:6.2f}           C"
    )
    lines.append("TER")
    lines.append("END")
    return "\n".join(lines) + "\n"


def _pdb_water_only(chain_id: str = "A") -> str:
    return textwrap.dedent(f"""
    HETATM    1  O   HOH {chain_id}   1       0.000   0.000   0.000  1.00 10.00           O
    TER
    END
    """).lstrip()


# ------------------------ tests ------------------------

def test__res3_to1_with_custom_and_bad():
    assert U._res3_to1("MSE") == "M"   # custom map
    assert U._res3_to1("SEC") == "U"
    assert U._res3_to1("PYL") == "O"
    assert U._res3_to1("ALA") == "A"
    # current implementation: empty string goes through Bio.SeqUtils.seq1("") → ""
    assert U._res3_to1(None) == ""


def test_load_structure_and_residue_count_and_mean_plddt():
    pdb = _pdb_three_residues()
    s = U.load_structure_from_pdb_text(pdb)
    assert U.residue_count(s) == 3
    mean = U.mean_plddt_from_ca_bfactor(s)
    assert math.isclose(mean, (90.0 + 80.0 + 70.0) / 3.0, rel_tol=1e-6)


def test_per_residue_plddt_ss_without_mkdssp(monkeypatch):
    pdb = _pdb_three_residues()
    s = U.load_structure_from_pdb_text(pdb)
    # force DSSP branch to fail, defaulting to coil "C"
    monkeypatch.setattr(structure_mod.shutil, "which", lambda _: None)
    plddts, sss, aas = U.per_residue_plddt_ss(s)
    assert plddts == [90.0, 80.0, 70.0]
    assert aas == ["A", "A", "A"]
    assert sss == ["C", "C", "C"]


def test_secondary_summary_from_structure_counts(monkeypatch):
    pdb = _pdb_three_residues()
    s = U.load_structure_from_pdb_text(pdb)
    monkeypatch.setattr(structure_mod.shutil, "which", lambda _: None)
    sec = U.secondary_summary_from_structure(s)
    assert sec.pct_coil == 100.0 and sec.pct_helix == 0.0 and sec.pct_sheet == 0.0
    assert sec.ss8_pct.get("C", 0) == 100.0


def test_primary_summary_from_sequence_empty_and_nonempty():
    p0 = U.primary_summary_from_sequence("")
    assert p0.length == 0
    seq = "ACDEFGHIKLMNPQRSTVWY"
    p = U.primary_summary_from_sequence(seq)
    assert p.length == 20
    assert abs(sum(p.aa_composition.values()) - 100.0) < 1e-6
    assert p.gravy is not None and p.isoelectric_point is not None
    assert p.pct_disorder == 0.0 and p.pct_low_complexity == 0.0
    assert p.has_signal_peptide is None and p.has_tm_segments is None


@pytest.mark.filterwarnings("ignore:Mean of empty slice:RuntimeWarning")
@pytest.mark.filterwarnings("ignore:invalid value encountered in scalar divide:RuntimeWarning")
def test_tertiary_summary_from_structure_bands_and_empty(monkeypatch):
    monkeypatch.setattr(structure_mod.shutil, "which", lambda _: None)
    pdb = _pdb_three_residues(b1=95, b2_a=75, b3=65)
    s = U.load_structure_from_pdb_text(pdb)
    plddts, _, _ = U.per_residue_plddt_ss(s)
    ter = U.tertiary_summary_from_structure(s, plddts)
    assert abs(sum(ter.plddt_bands.values()) - 100.0) < 1e-6
    # empty list → mean is NaN; check with isnan
    ter0 = U.tertiary_summary_from_structure(s, [])
    assert math.isnan(ter0.mean_plddt)


def test_get_protein_chain_select_and_errors():
    pdb = _pdb_three_residues(chain_id="B")
    s = U.load_structure_from_pdb_text(pdb)
    assert U.get_protein_chain(s, "B").id == "B"
    with pytest.raises(ValueError):
        U.get_protein_chain(s, "Z")
    s2 = U.load_structure_from_pdb_text(_pdb_water_only("A"))
    with pytest.raises(ValueError):
        U.get_protein_chain(s2)


def test_best_ca_picks_altloc_with_higher_occupancy():
    pdb = _pdb_three_residues(b2_b=60.0)
    s = U.load_structure_from_pdb_text(pdb)
    model = s[0]
    chain = next(iter(model))
    res2 = [r for r in chain if r.id[1] == 2][0]
    ca = U.best_ca(res2)
    assert ca is not None and abs(ca.get_coord()[0] - 1.2) < 1e-6


def test_kabsch_and_pairs_success_and_insufficient_pairs():
    pdb_pred = _pdb_three_residues(chain_id="A")
    pdb_ref = _pdb_three_residues(chain_id="A", offset=(2.0, -3.0, 1.0))
    rmsd, n_pairs, ref_arr, pred_arr, seq_id, gap_frac = U.kabsch_and_pairs(
        pdb_pred, pdb_ref
    )
    assert n_pairs == 3
    assert ref_arr.shape == pred_arr.shape == (3, 3)
    assert 0.99 <= seq_id <= 1.0
    assert 0.0 <= gap_frac <= 1.0
    assert rmsd < 1e-6
    # insufficient pairs (only first atom line kept) → <3 pairs
    pdb_small = "\n".join(pdb_pred.splitlines()[:2] + ["TER", "END\n"])
    with pytest.raises(ValueError):
        U.kabsch_and_pairs(pdb_small, pdb_small)


def test_gdt_ts_and_gdt_ha_and_shape_errors():
    ref = np.array([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0]])
    pred = ref.copy()
    assert U.gdt_ts(ref, pred) == 100.0
    assert U.gdt_ha(ref, pred) == 100.0
    z = np.zeros((0, 3))
    assert U.gdt_ts(z, z) == 0.0
    assert U.gdt_ha(z, z) == 0.0
    with pytest.raises(ValueError):
        U.gdt_ts(ref, pred[:2])


def test_tm_score_various():
    ref = np.array([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0]])
    pred = ref.copy()
    # IMPORTANT: choose l_ref >= 15 to avoid negative base in (l_ref-15) ** (1/3)
    t = U.tm_score(ref, pred, l_ref=30)
    assert 0.9 <= t <= 1.0
    # empty → 0.0
    z = np.zeros((0, 3))
    assert U.tm_score(z, z, l_ref=0) == 0.0
    with pytest.raises(ValueError):
        U.tm_score(ref, pred[:2])


def test_low_confidence_segments_edges():
    p = [50]*8 + [80]*2 + [40]*10
    assert U.low_confidence_segments(p, thresh=70, min_len=8) == [(0, 8), (10, 20)]
    p = [80, 60, 60, 60, 60, 60, 60, 60]
    assert U.low_confidence_segments(p, thresh=70, min_len=7) == [(1, 8)]
    assert U.low_confidence_segments([60, 60, 60], thresh=70, min_len=4) == []


def test_compute_metrics_without_and_with_reference(monkeypatch):
    # Force DSSP-off branch to keep tests fast & deterministic
    monkeypatch.setattr(structure_mod.shutil, "which", lambda _: None)

    # No reference path (3 residues)
    seq = "AAA"
    pred = _pdb_three_residues()
    out = U.compute_metrics(seq, pred, ref_pdb_text=None)
    assert out.primary.length == 3
    assert out.secondary.pct_coil == 100.0
    assert out.tertiary.mean_plddt > 0

    # With reference: use ≥20 residues to avoid tm_score negative-base issue
    n = 20
    seq2 = "A" * n
    pred2 = _pdb_n_residues(n, chain_id="A", bfactor=85.0)
    ref2  = _pdb_n_residues(n, chain_id="A", bfactor=85.0, offset=(1.0, 2.0, -1.0))
    out2 = U.compute_metrics(seq2, pred2, ref_pdb_text=ref2)
    assert out2.ref_residues == n
    assert out2.n_matched_pairs == n
    assert out2.tertiary.rmsd < 1e-6
    assert 0.0 <= out2.tertiary.gdt_ts <= 100.0
    assert 0.0 <= out2.tertiary.gdt_ha <= 100.0
    assert 0.0 <= out2.tertiary.tm_score <= 1.0
    # lengths are equal → q3 computed
    assert out2.secondary.q3 is not None

    # Mismatched lengths → q3 None
    ref_small = _pdb_n_residues(n - 1, chain_id="A", bfactor=85.0)
    out3 = U.compute_metrics(seq2, pred2, ref_pdb_text=ref_small)
    assert out3.secondary.q3 is None
