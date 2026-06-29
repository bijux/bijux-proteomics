# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protease registry and digestion policy helpers."""

from __future__ import annotations

import hashlib
import json

from bijux_proteomics.sequences.digestion.models import (
    DigestPolicy,
    PeptideDigestionMode,
    ProteaseCleavageMode,
    ProteaseRule,
)

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
    "aspn": ProteaseRule(
        name="aspn",
        cleavage_mode=ProteaseCleavageMode.N_TERMINAL,
        cleavage_residues="D",
        blocked_by_previous="P",
        description="Cleaves before aspartate unless preceded by proline.",
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


def resolve_protease_rule(
    name: str | None = None,
    *,
    custom_specification: str | None = None,
    custom_name: str = "custom",
) -> ProteaseRule:
    """Resolve either one built-in protease or one explicit custom rule."""

    has_name = name is not None and name.strip() != ""
    has_custom = custom_specification is not None and custom_specification.strip() != ""
    if has_name == has_custom:
        raise ValueError(
            "provide exactly one of a built-in protease name or a custom protease specification"
        )
    if has_custom:
        return parse_custom_protease_rule(
            str(custom_specification),
            name=custom_name,
        )
    if name is None:
        raise ValueError("protease name must be provided when no custom rule is used")
    return get_protease_rule(name)


def parse_custom_protease_rule(
    specification: str, *, name: str = "custom"
) -> ProteaseRule:
    """Parse a user-defined protease rule from a compact textual form."""

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
    pattern = fields.get("pattern")
    cut_after = fields.get("cut_after")
    cut_before = fields.get("cut_before")

    has_residue_rule = bool(after) or bool(before)
    has_regex_rule = bool(pattern) or bool(cut_after) or bool(cut_before)
    if has_residue_rule and has_regex_rule:
        raise ValueError(
            "custom protease rule must use either residue keys or regex keys, not both"
        )
    if not has_residue_rule and not has_regex_rule:
        raise ValueError(
            "custom protease rule must define exactly one cleavage direction using residue cleavage keys or regex cleavage keys"
        )

    if has_regex_rule:
        if not pattern:
            raise ValueError("regex protease rules must define 'pattern'")
        if bool(cut_after) == bool(cut_before):
            raise ValueError(
                "regex protease rule must define exactly one of 'cut_after' or 'cut_before'"
            )
        if "block_next" in fields or "block_previous" in fields:
            raise ValueError(
                "regex protease rules must encode blocking behavior inside 'pattern'"
            )
        return ProteaseRule(
            name=name,
            cleavage_mode=(
                ProteaseCleavageMode.C_TERMINAL
                if cut_after is not None
                else ProteaseCleavageMode.N_TERMINAL
            ),
            cleavage_pattern=pattern,
            cleavage_cut_side="after" if cut_after is not None else "before",
            cleavage_group=(cut_after or cut_before or "0"),
            description=fields.get("description", ""),
        )

    if bool(after) == bool(before):
        raise ValueError(
            "custom protease rule must define exactly one of 'after' or 'before'"
        )
    cleavage_mode = (
        ProteaseCleavageMode.C_TERMINAL
        if after is not None
        else ProteaseCleavageMode.N_TERMINAL
    )
    cleavage_residues = after if after is not None else before
    if cleavage_residues is None:
        raise ValueError("custom protease rule must resolve to a cleavage residue set")
    return ProteaseRule(
        name=name,
        cleavage_mode=cleavage_mode,
        cleavage_residues=cleavage_residues,
        blocked_by_next=fields.get("block_next", ""),
        blocked_by_previous=fields.get("block_previous", ""),
        description=fields.get("description", ""),
    )


def build_digest_policy(
    *,
    protease: str | ProteaseRule,
    digestion_mode: PeptideDigestionMode,
    missed_cleavages: int,
    min_length: int | None,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
) -> DigestPolicy:
    """Build one stable digestion policy from a protease selection and filters."""

    rule = get_protease_rule(protease) if isinstance(protease, str) else protease
    return DigestPolicy(
        protease=rule.name,
        cleavage_mode=rule.cleavage_mode,
        cleavage_residues=rule.cleavage_residues,
        blocked_by_next=rule.blocked_by_next,
        blocked_by_previous=rule.blocked_by_previous,
        cleavage_pattern=rule.cleavage_pattern,
        cleavage_cut_side=rule.cleavage_cut_side,
        cleavage_group=rule.cleavage_group,
        digestion_mode=digestion_mode,
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )


def compute_digest_policy_hash(policy: DigestPolicy) -> str:
    """Return a stable fingerprint over one digestion policy."""

    return hashlib.sha256(
        json.dumps(policy.to_dict(), sort_keys=True).encode("utf-8")
    ).hexdigest()


__all__ = [
    "DigestPolicy",
    "PeptideDigestionMode",
    "ProteaseCleavageMode",
    "ProteaseRule",
    "build_digest_policy",
    "compute_digest_policy_hash",
    "get_protease_rule",
    "parse_custom_protease_rule",
    "protease_registry",
    "resolve_protease_rule",
]
