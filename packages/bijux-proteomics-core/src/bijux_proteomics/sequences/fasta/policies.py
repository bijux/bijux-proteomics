# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Residue policy and identifier helpers for FASTA intake."""

from __future__ import annotations

import hashlib

from bijux_proteomics.sequences.fasta.models import (
    _DECOY_PREFIXES,
    _ENSEMBL_ACCESSION_RE,
    _REFSEQ_ACCESSION_RE,
    _UNIPROT_ACCESSION_RE,
    FastaParseMode,
    ResiduePolicyEntry,
    ResiduePolicyState,
    SequenceResiduePolicy,
    UniProtAccession,
)

_SEQUENCE_POLICY_BY_MODE: dict[FastaParseMode, SequenceResiduePolicy] = {
    FastaParseMode.STRICT: SequenceResiduePolicy(
        mode=FastaParseMode.STRICT,
        entries=(
            ResiduePolicyEntry(
                residue="B",
                state=ResiduePolicyState.REFUSED,
                rationale="B conflates aspartate and asparagine and is refused in strict mode.",
            ),
            ResiduePolicyEntry(
                residue="J",
                state=ResiduePolicyState.REFUSED,
                rationale="J conflates leucine and isoleucine and is refused in strict mode.",
            ),
            ResiduePolicyEntry(
                residue="X",
                state=ResiduePolicyState.REFUSED,
                rationale="X does not preserve residue identity and is refused in strict mode.",
            ),
            ResiduePolicyEntry(
                residue="Z",
                state=ResiduePolicyState.REFUSED,
                rationale="Z conflates glutamate and glutamine and is refused in strict mode.",
            ),
            ResiduePolicyEntry(
                residue="U",
                state=ResiduePolicyState.REFUSED,
                rationale="U is currently unsupported by downstream chemistry surfaces.",
            ),
            ResiduePolicyEntry(
                residue="O",
                state=ResiduePolicyState.REFUSED,
                rationale="O is currently unsupported by downstream chemistry surfaces.",
            ),
        ),
    ),
    FastaParseMode.PERMISSIVE: SequenceResiduePolicy(
        mode=FastaParseMode.PERMISSIVE,
        entries=(
            ResiduePolicyEntry(
                residue="B",
                state=ResiduePolicyState.ACCEPTED_WITH_WARNING,
                rationale="B is preserved with warning because it is residue-ambiguous.",
            ),
            ResiduePolicyEntry(
                residue="J",
                state=ResiduePolicyState.ACCEPTED_WITH_WARNING,
                rationale="J is preserved with warning because it is residue-ambiguous.",
            ),
            ResiduePolicyEntry(
                residue="X",
                state=ResiduePolicyState.ACCEPTED_WITH_WARNING,
                rationale="X is preserved with warning because it is residue-ambiguous.",
            ),
            ResiduePolicyEntry(
                residue="Z",
                state=ResiduePolicyState.ACCEPTED_WITH_WARNING,
                rationale="Z is preserved with warning because it is residue-ambiguous.",
            ),
            ResiduePolicyEntry(
                residue="U",
                state=ResiduePolicyState.REFUSED,
                rationale="U remains refused until chemistry and mass surfaces support it explicitly.",
            ),
            ResiduePolicyEntry(
                residue="O",
                state=ResiduePolicyState.REFUSED,
                rationale="O remains refused until chemistry and mass surfaces support it explicitly.",
            ),
        ),
    ),
}


def build_sequence_residue_policy(mode: FastaParseMode) -> SequenceResiduePolicy:
    """Return the explicit uncommon-residue policy for one parser mode."""

    return _SEQUENCE_POLICY_BY_MODE[mode].model_copy(deep=True)


def sequence_checksum(residues: str) -> str:
    """Return a stable SHA-256 checksum over normalized residues."""

    normalized = "".join(
        character for character in residues.strip().upper() if not character.isspace()
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_uniprot_accession(value: str) -> UniProtAccession:
    """Normalize one UniProt accession token, preserving isoform suffixes."""

    token = value.strip().upper()
    match = _UNIPROT_ACCESSION_RE.fullmatch(token)
    if match is None:
        raise ValueError("value must be a valid UniProt accession")
    isoform = match.group("isoform")
    return UniProtAccession(
        accession=match.group("accession"),
        isoform=int(isoform) if isoform is not None else None,
    )


def canonicalize_protein_reference(value: str) -> str:
    """Normalize one protein reference token onto the canonical accession surface."""

    _namespace, canonical_accession, _isoform = _normalize_accession(value)
    return canonical_accession


def _normalize_accession(identifier: str) -> tuple[str, str, int | None]:
    token = identifier.strip()
    decoy_prefix = next(
        (prefix for prefix in _DECOY_PREFIXES if token.upper().startswith(prefix)),
        "",
    )
    normalized_token = token[len(decoy_prefix) :] if decoy_prefix else token
    if "|" in normalized_token:
        parts = normalized_token.split("|")
        if len(parts) >= 3 and parts[0] in {"sp", "tr"}:
            accession = parse_uniprot_accession(parts[1])
            return "uniprot", f"{decoy_prefix}{accession.accession}", accession.isoform
        if len(parts) >= 3 and parts[0] in {"ref", "gb"}:
            refseq = parts[1].upper()
            if _REFSEQ_ACCESSION_RE.fullmatch(refseq):
                return "refseq", f"{decoy_prefix}{refseq}", None
    candidate = normalized_token.upper()
    if _UNIPROT_ACCESSION_RE.fullmatch(candidate):
        accession = parse_uniprot_accession(candidate)
        return "uniprot", f"{decoy_prefix}{accession.accession}", accession.isoform
    if _REFSEQ_ACCESSION_RE.fullmatch(candidate):
        return "refseq", f"{decoy_prefix}{candidate}", None
    if match := _ENSEMBL_ACCESSION_RE.fullmatch(candidate):
        return "ensembl", f"{decoy_prefix}{match.group('accession')}", None
    return "custom", token, None


__all__ = [
    "FastaParseMode",
    "UniProtAccession",
    "build_sequence_residue_policy",
    "canonicalize_protein_reference",
    "parse_uniprot_accession",
    "sequence_checksum",
]
