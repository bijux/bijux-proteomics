# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.digestion import PeptideDigestionMode, get_protease_rule
from bijux_proteomics.enzyme_rule_provenance import (
    EnzymeRuleSupportState,
    build_enzyme_rule_provenance,
)


def test_build_enzyme_rule_provenance_records_mode_and_support_state() -> None:
    gluc = get_protease_rule("gluc")
    report = build_enzyme_rule_provenance(
        rule=gluc,
        digestion_mode=PeptideDigestionMode.SEMI_SPECIFIC,
        source="study policy",
    )

    assert report.rule_name == "gluc"
    assert report.cleavage_mode == "c_terminal"
    assert report.cleavage_residues == "E"
    assert report.support_state is EnzymeRuleSupportState.ADVISORY
    assert "semi-specific digestion is advisory" in report.notes[0]


def test_build_enzyme_rule_provenance_marks_unsupported_rules_with_reason() -> None:
    trypsin = get_protease_rule("trypsin")
    report = build_enzyme_rule_provenance(
        rule=trypsin,
        digestion_mode=PeptideDigestionMode.FULL,
        source="legacy import",
        unsupported_reason="legacy vendor digest rule omitted cleavage exceptions",
    )

    assert report.support_state is EnzymeRuleSupportState.UNSUPPORTED
    assert report.notes[-1] == "legacy vendor digest rule omitted cleavage exceptions"
