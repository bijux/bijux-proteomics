# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Sequence-level utilities."""

from __future__ import annotations

import numpy as np

from agentic_proteins.report import PrimarySummary

# Hydropathy values for GRAVY (Kyte-Doolittle)
HYDROPATHY = {
    "A": 1.8,
    "C": 2.5,
    "D": -3.5,
    "E": -3.5,
    "F": 2.8,
    "G": -0.4,
    "H": -3.2,
    "I": 4.5,
    "K": -3.9,
    "L": 3.8,
    "M": 1.9,
    "N": -3.5,
    "P": -1.6,
    "Q": -3.5,
    "R": -4.5,
    "S": -0.8,
    "T": -0.7,
    "V": 4.2,
    "W": -0.9,
    "Y": -1.3,
}
"""Dictionary of hydropathy values for amino acids used in GRAVY calculation."""

# Approximate pKa for pI calculation (simple average for charged residues)
PKA_N_TERM = 9.0
"""Approximate pKa value for N-terminus."""

PKA_C_TERM = 2.0
"""Approximate pKa value for C-terminus."""

PKA_SIDE = {"D": 3.9, "E": 4.3, "H": 6.0, "C": 8.3, "Y": 10.1, "K": 10.5, "R": 12.5}
"""Dictionary of approximate pKa values for side chains of charged amino acids."""


def primary_summary_from_sequence(sequence: str) -> PrimarySummary:
    """Computes primary structure summary from the sequence.

    Args:
        sequence: The amino acid sequence string.

    Returns:
        PrimarySummary object.
    """
    n = len(sequence)
    if n == 0:
        return PrimarySummary(length=0)
    aa_composition = {}
    for aa in sequence:
        aa_composition[aa] = aa_composition.get(aa, 0) + 1
    aa_composition = {k: 100.0 * v / n for k, v in aa_composition.items()}
    gravy = np.mean([HYDROPATHY.get(aa, 0.0) for aa in sequence])
    # Simple pI approximation (average pKa)
    pos = sum(sequence.count(aa) for aa in "KRH")
    neg = sum(sequence.count(aa) for aa in "DEC")
    pi_val = (
        (PKA_N_TERM + PKA_C_TERM) / 2
        if pos == neg == 0
        else (9.0 * pos + 4.0 * neg) / (pos + neg)
    )  # Rough
    # pct_disorder and pct_low_complexity would require tools; leave None or implement simple entropy-based
    pct_low_complexity = 0.0  # Placeholder
    pct_disorder = 0.0  # Placeholder
    has_signal_peptide = None  # Would require tools like SignalP or similar
    has_tm_segments = None  # TMHMM or similar
    return PrimarySummary(
        length=n,
        aa_composition=aa_composition,
        gravy=gravy,
        isoelectric_point=pi_val,
        pct_disorder=pct_disorder,
        pct_low_complexity=pct_low_complexity,
        has_signal_peptide=has_signal_peptide,
        has_tm_segments=has_tm_segments,
    )
