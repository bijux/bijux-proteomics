# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein digestion and peptide indexing contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation import JsonModel


class ProteaseCleavageMode(StrEnum):
    """Direction for protease cleavage semantics."""

    C_TERMINAL = "c_terminal"
    N_TERMINAL = "n_terminal"


class ProteaseRule(JsonModel):
    """Stable cleavage contract for one protease."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    cleavage_mode: ProteaseCleavageMode = ProteaseCleavageMode.C_TERMINAL
    cleavage_residues: str = Field(..., min_length=1)
    blocked_by_next: str = ""
    blocked_by_previous: str = ""
    description: str = ""

    @field_validator("cleavage_residues", "blocked_by_next", "blocked_by_previous")
    @classmethod
    def _normalize_residue_token(cls, value: str) -> str:
        return "".join(sorted(set(value.strip().upper())))


_PROTEASE_REGISTRY: dict[str, ProteaseRule] = {
    "trypsin": ProteaseRule(
        name="trypsin",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="KR",
        blocked_by_next="P",
        description="Cleaves after lysine or arginine unless followed by proline.",
    ),
    "lysc": ProteaseRule(
        name="lysc",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="K",
        blocked_by_next="P",
        description="Cleaves after lysine unless followed by proline.",
    ),
    "argc": ProteaseRule(
        name="argc",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="R",
        blocked_by_next="P",
        description="Cleaves after arginine unless followed by proline.",
    ),
    "gluc": ProteaseRule(
        name="gluc",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="E",
        blocked_by_next="P",
        description="Cleaves after glutamate unless followed by proline.",
    ),
    "chymotrypsin": ProteaseRule(
        name="chymotrypsin",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="FWYL",
        blocked_by_next="P",
        description="Cleaves after aromatic residues unless followed by proline.",
    ),
}


def protease_registry() -> dict[str, ProteaseRule]:
    """Return the built-in protease rule registry."""
    return dict(_PROTEASE_REGISTRY)


def get_protease_rule(name: str) -> ProteaseRule:
    """Return one built-in protease rule by normalized name."""
    normalized = name.strip().lower().replace("-", "").replace("_", "")
    try:
        return _PROTEASE_REGISTRY[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown protease rule {name!r}") from exc


def parse_custom_protease_rule(specification: str, *, name: str = "custom") -> ProteaseRule:
    """Parse a user-defined protease rule from a compact textual form.

    Supported keys:
    - ``after`` or ``before`` for cleavage residues
    - ``block_next`` for residues that block a C-terminal cut
    - ``block_previous`` for residues that block an N-terminal cut
    - ``description`` for human-readable metadata
    """

    fields: dict[str, str] = {}
    for fragment in specification.split(";"):
        token = fragment.strip()
        if not token:
            continue
        key, separator, value = token.partition("=")
        if not separator:
            raise ValueError(
                "custom protease rules must use key=value fragments separated by semicolons"
            )
        fields[key.strip().lower()] = value.strip()

    after = fields.get("after")
    before = fields.get("before")
    if bool(after) == bool(before):
        raise ValueError("custom protease rule must define exactly one of 'after' or 'before'")

    cleavage_mode = (
        ProteaseCleavageMode.C_TERMINAL if after is not None else ProteaseCleavageMode.N_TERMINAL
    )
    cleavage_residues = after if after is not None else before
    assert cleavage_residues is not None
    return ProteaseRule(
        name=name,
        cleavage_mode=cleavage_mode,
        cleavage_residues=cleavage_residues,
        blocked_by_next=fields.get("block_next", ""),
        blocked_by_previous=fields.get("block_previous", ""),
        description=fields.get("description", ""),
    )
