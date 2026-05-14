from __future__ import annotations

import pytest

from bijux_proteomics.sequences.digestion import (
    ProteaseCleavageMode,
    get_protease_rule,
    parse_custom_protease_rule,
    protease_registry,
    resolve_protease_rule,
)


def test_protease_registry_exposes_expected_builtin_rules() -> None:
    registry = protease_registry()

    assert {"trypsin", "lysc", "gluc", "argc", "chymotrypsin", "aspn"} <= set(registry)
    assert registry["trypsin"].cleavage_residues == "KR"
    assert registry["trypsin"].blocked_by_next == "P"
    assert registry["aspn"].cleavage_mode is ProteaseCleavageMode.N_TERMINAL
    assert registry["aspn"].blocked_by_previous == "P"


def test_get_protease_rule_normalizes_common_name_variants() -> None:
    rule = get_protease_rule("Lys-C")
    aspn = get_protease_rule("Asp-N")

    assert rule.name == "lysc"
    assert rule.cleavage_mode is ProteaseCleavageMode.C_TERMINAL
    assert aspn.name == "aspn"
    assert aspn.cleavage_mode is ProteaseCleavageMode.N_TERMINAL


def test_parse_custom_protease_rule_supports_c_terminal_and_n_terminal_modes() -> None:
    c_terminal = parse_custom_protease_rule(
        "after=KR;block_next=P;description=trypsin-like",
        name="custom-trypsin",
    )
    n_terminal = parse_custom_protease_rule(
        "before=DE;block_previous=P",
        name="custom-acidic",
    )

    assert c_terminal.name == "custom-trypsin"
    assert c_terminal.cleavage_mode is ProteaseCleavageMode.C_TERMINAL
    assert c_terminal.blocked_by_next == "P"
    assert n_terminal.cleavage_mode is ProteaseCleavageMode.N_TERMINAL
    assert n_terminal.cleavage_residues == "DE"


def test_parse_custom_protease_rule_requires_exactly_one_cleavage_direction() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        parse_custom_protease_rule("after=KR;before=DE")

    with pytest.raises(ValueError, match="exactly one"):
        parse_custom_protease_rule("block_next=P")


def test_resolve_protease_rule_supports_builtin_and_custom_paths() -> None:
    builtin = resolve_protease_rule("Arg-C")
    custom = resolve_protease_rule(
        custom_specification="before=D;block_previous=P",
        custom_name="custom-aspn-like",
    )

    assert builtin.name == "argc"
    assert custom.name == "custom-aspn-like"
    assert custom.cleavage_mode is ProteaseCleavageMode.N_TERMINAL


def test_resolve_protease_rule_requires_exactly_one_rule_source() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        resolve_protease_rule("trypsin", custom_specification="after=KR")

    with pytest.raises(ValueError, match="exactly one"):
        resolve_protease_rule(None)
