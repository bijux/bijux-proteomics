# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""
Prep examples/ from RCSB PDB: per-chain FASTA + ground-truth PDB.

Usage:
  python scripts/manage_examples.py [--targets 4krp:B 2zta:A,B ...] [--out examples] [--skip-existing] [--force]

Outputs, e.g.:
  examples/ex01_4krp_B/
    - 4krp.pdb (raw) or .cif if PDB unavailable
    - 4krp.fasta (raw entry FASTA)
    - seq_4krp_chainB.fasta
    - ground_truth_4krp_B.pdb
    - meta.json
    (+ combined PDB/FASTA if multiple chains requested)

Requires: requests, biopython
  pip install requests biopython
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import re
import textwrap
import time
from io import StringIO
from typing import Dict, List, Optional, Set, Tuple

import requests
from Bio import SeqIO
from Bio.PDB import PDBIO, PDBParser, Select
from Bio.PDB.MMCIFParser import MMCIFParser
from Bio.PDB.Polypeptide import is_aa

# ------------------- CONFIG -------------------

DEFAULT_TARGETS = [
    "4krp:B",  # example from your message
    "1ubq:A",
    "1crn",
    "1yrf:A",
    "1qys:A",
    "2n0a:A",  # IDP-ish case
    "2zta:A,B",  # coiled-coil dimer
    "2rh1:A",  # GPCR
    "2omf:A",  # β-barrel
    "1a3n:B",  # hemoglobin β chain
]

DEFAULT_OUT_ROOT = pathlib.Path("examples")
PAUSE_SEC_BETWEEN_DOWNLOADS = 0.25  # be gentle to RCSB
HTTP_TIMEOUT = 30
HTTP_RETRIES = 3
USER_AGENT = "agentic-proteins-example-prep/1.0 (+https://rcsb.org)"


# ------------------- HTTP HELPERS -------------------

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})


def _get(url: str, timeout: float = HTTP_TIMEOUT) -> requests.Response:
    last_err = None
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            r = _session.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_err = e
            if attempt < HTTP_RETRIES:
                time.sleep(0.6 * attempt)
            else:
                raise
    raise last_err  # just in case


# ------------------- RCSB HELPERS -------------------


def fetch_structure_text(pdb_id: str) -> Tuple[str, str]:
    """Return (format, text) where format is 'pdb' or 'cif'."""
    pdb_url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
    cif_url = f"https://files.rcsb.org/download/{pdb_id.upper()}.cif"
    try:
        txt = _get(pdb_url).text
        return "pdb", txt
    except requests.RequestException:
        txt = _get(cif_url).text  # let this raise if not available
        return "cif", txt


def fetch_entry_fasta(pdb_id: str) -> str:
    # Entry FASTA contains one record per polymer chain
    url = f"https://www.rcsb.org/fasta/entry/{pdb_id.upper()}/display?format=fasta"
    return _get(url).text


def parse_fasta_per_chain(fasta_text: str) -> Dict[str, str]:
    chain_to_seq: Dict[str, str] = {}
    saw_any = False

    for rec in SeqIO.parse(StringIO(fasta_text), "fasta"):
        saw_any = True
        desc = rec.description.lstrip("> ").strip()
        parts = [p.strip() for p in desc.split("|")]
        if len(parts) < 2:
            continue

        chain_part = parts[1]  # e.g. "Chain A" or "Chains A, B" or "Chains A and B"
        m = re.match(r"Chain(s)?\s+(.+)", chain_part, flags=re.IGNORECASE)
        if not m:
            continue

        chain_str = m.group(2)
        # normalize separators: "A and B" / "A; B" / "A , B" -> "A,B"
        chain_str = re.sub(r"\band\b", ",", chain_str, flags=re.IGNORECASE)
        chain_str = chain_str.replace(";", ",")
        chain_str = re.sub(r"\s*,\s*", ",", chain_str)

        chains = []
        for ch in chain_str.split(","):
            ch = re.sub(r"\[.*?\]", "", ch).strip()  # drop annotations like [auth B]
            ch = re.sub(
                r"^Chain\s+", "", ch, flags=re.I
            )  # drop stray "Chain " prefixes
            if ch:
                chains.append(ch)

        if chains:
            seq = str(rec.seq)
            for ch in chains:
                chain_to_seq[ch] = seq
        else:
            # fallback: parse IDs like '4KRP:A' in rec.id
            m2 = re.search(r":([A-Za-z0-9])$", rec.id)
            if m2 and (rec_id := m2.group(1)):
                chain_to_seq[rec_id] = str(rec.seq)

    if not chain_to_seq and saw_any:
        try:
            first_desc = next(SeqIO.parse(StringIO(fasta_text), "fasta")).description
            print(
                "  ! FASTA headers unrecognized. First header was:",
                (first_desc or "")[:140],
            )
        except StopIteration:
            print("  ! FASTA headers unrecognized and file appears empty.")

    return chain_to_seq


def detect_protein_chains(structure_text: str, fmt: str) -> List[str]:
    """Find chain IDs that contain amino acid residues."""
    if fmt == "pdb":
        parser = PDBParser(QUIET=True)
    else:
        parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure("entry", StringIO(structure_text))
    chains: Set[str] = set()
    for chain in structure.get_chains():
        for res in chain:
            if is_aa(res):
                chains.add(chain.id)
                break
    return sorted(chains)


# ------------------- STRUCTURE CHAIN WRITER -------------------


class ChainSelect(Select):
    def __init__(self, wanted: Set[str]):
        super().__init__()
        self.wanted = wanted

    def accept_chain(self, chain):
        return chain.id in self.wanted


def write_chain_subset_structure(
    structure_text: str, fmt: str, chains: List[str], out_path: pathlib.Path
) -> None:
    if fmt == "pdb":
        parser = PDBParser(QUIET=True)
    else:
        parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure("entry", StringIO(structure_text))
    present = {c.id for c in structure.get_chains()}
    missing = [c for c in chains if c not in present]
    if missing:
        raise RuntimeError(
            f"Requested chain(s) not present in structure: {','.join(missing)}"
        )
    io = PDBIO()
    io.set_structure(structure)
    io.save(str(out_path), select=ChainSelect(set(chains)))


# ------------------- UTIL -------------------


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def parse_target(t: str) -> Tuple[str, Optional[List[str]]]:
    """'4krp:B,C' -> ('4krp', ['B','C']); '1ubq' -> ('1ubq', None)"""
    s = t.strip()
    if ":" in s:
        pdb_id, chains = s.split(":", 1)
        chains = re.split(r"[,+]", chains.strip())
        chains = [c.strip() for c in chains if c.strip()]
        return pdb_id.lower(), chains
    return s.lower(), None


def _write(p: pathlib.Path, text: str, force: bool) -> None:
    if p.exists() and not force:
        return
    p.write_text(text, encoding="utf-8", newline="\n")


# ------------------- MAIN WORK -------------------


def prepare_example(
    idx: int,
    target: str,
    out_root: pathlib.Path,
    skip_existing: bool = False,
    force: bool = False,
) -> None:
    pdb_id, user_chains = parse_target(target)
    print(f"[{idx:02d}] Preparing {pdb_id.upper()} (chains: {user_chains or 'auto'})")

    # fetch data
    fmt, structure_text = fetch_structure_text(pdb_id)
    time.sleep(PAUSE_SEC_BETWEEN_DOWNLOADS * (1.0 + 0.5 * random.random()))
    fasta_text = fetch_entry_fasta(pdb_id)
    time.sleep(PAUSE_SEC_BETWEEN_DOWNLOADS * (1.0 + 0.5 * random.random()))

    # parse chains/sequences
    fasta_chains = parse_fasta_per_chain(fasta_text)
    if not fasta_chains:
        raise RuntimeError(f"No FASTA chains parsed for {pdb_id}")
    detected_chains = detect_protein_chains(structure_text, fmt)
    if not detected_chains:
        detected_chains = sorted(list(fasta_chains.keys()))  # fallback

    # determine chains to process
    chains = user_chains or detected_chains
    if not chains:
        raise RuntimeError("No protein chains found; this may not be a protein entry.")

    chains_tag = "+".join(chains)

    # folder
    ex_dir = out_root / f"ex{idx:02d}_{pdb_id.lower()}_{chains_tag}"
    if skip_existing and ex_dir.exists():
        print(f"  ↷ skipping (exists): {ex_dir}")
        return
    ex_dir.mkdir(parents=True, exist_ok=True)

    # write provenance files
    structure_file = ex_dir / f"{pdb_id.lower()}.{fmt}"
    _write(structure_file, structure_text, force)
    _write(ex_dir / f"{pdb_id.lower()}.fasta", fasta_text, force)

    # write meta
    meta = {
        "pdb_id": pdb_id.upper(),
        "chains_requested": user_chains,
        "chains_detected": detected_chains,
        "fasta_chains_available": sorted(list(fasta_chains.keys())),
        "structure_format": fmt,
        "sources": {
            "structure_url": f"https://files.rcsb.org/download/{pdb_id.upper()}.{fmt}",
            "fasta_url": f"https://www.rcsb.org/fasta/entry/{pdb_id.upper()}/display?format=fasta",
            "rcsb_entry": f"https://www.rcsb.org/structure/{pdb_id.upper()}",
        },
        "checksums": {
            "entry_structure_md5": _md5(structure_text),
            "entry_fasta_md5": _md5(fasta_text),
        },
    }
    _write(ex_dir / "meta.json", json.dumps(meta, indent=2), force)

    # write per-chain FASTAs + ground-truth PDBs
    for ch in chains:
        seq = fasta_chains.get(ch)
        if not seq:
            print(f"  ! chain {ch}: sequence not found in FASTA; skipping FASTA write")
        else:
            fasta_path = ex_dir / f"seq_{pdb_id.lower()}_chain{ch}.fasta"
            fasta_body = f">{pdb_id.upper()}:{ch}\n{textwrap.fill(seq, 80)}\n"
            _write(fasta_path, fasta_body, force)

        gt_path = ex_dir / f"ground_truth_{pdb_id.lower()}_{ch}.pdb"
        write_chain_subset_structure(structure_text, fmt, [ch], gt_path)
        print(f"  ✓ chain {ch}: FASTA{' ✓' if seq else ' (missing)'} | PDB ✓")

    # if multiple chains requested, also write a combined ground-truth PDB (+ multi-FASTA if possible)
    if len(chains) >= 2:
        combo_name = "+".join(chains)
        combo_gt = ex_dir / f"ground_truth_{pdb_id.lower()}_{combo_name}.pdb"
        write_chain_subset_structure(structure_text, fmt, chains, combo_gt)

        if all(ch in fasta_chains for ch in chains):
            mfasta_lines = []
            for ch in chains:
                mfasta_lines.append(f">{pdb_id.upper()}:{ch}")
                mfasta_lines.append(textwrap.fill(fasta_chains[ch], 80))
            mfasta_path = ex_dir / f"seq_{pdb_id.lower()}_{combo_name}.fasta"
            _write(mfasta_path, "\n".join(mfasta_lines) + "\n", force)
        print(f"  ✓ combined {combo_name}: PDB ✓ (+ multi-FASTA if available)")


def main():
    parser = argparse.ArgumentParser(description="Prepare PDB examples from RCSB")
    parser.add_argument(
        "--targets",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="PDB targets (e.g., 4krp:B 2zta:A,B); default from script",
    )
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=DEFAULT_OUT_ROOT,
        help="Output root directory",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip if example dir already exists",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of existing files (otherwise, skip writing if file exists)",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    for i, tgt in enumerate(args.targets, start=1):
        try:
            prepare_example(i, tgt, args.out, args.skip_existing, args.force)
        except Exception as e:
            print(f"[{i:02d}] ERROR for {tgt}: {e}")


if __name__ == "__main__":
    main()
