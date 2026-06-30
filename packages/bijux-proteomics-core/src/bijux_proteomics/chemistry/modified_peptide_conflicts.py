# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Advanced modified-peptide conflict checks with chemistry-aware refusals."""

from __future__ import annotations

from collections import defaultdict

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.contracts.models import (
    ModificationPosition,
    ParsedModifiedPeptide,
)
from bijux_proteomics_foundation import JsonModel


class ModifiedPeptideConflictIssue(JsonModel):
    """One conflict issue for a modified-peptide hypothesis."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    involved_modifications: tuple[str, ...] = Field(default_factory=tuple)


class ModifiedPeptideConflictReport(JsonModel):
    """Validation report for modified-peptide conflicts."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: tuple[ModifiedPeptideConflictIssue, ...] = Field(default_factory=tuple)


_TERMINAL_LABEL_TOKENS = {
    "acetyl",
    "tmt6plex",
    "tmt10plex",
    "tmt11plex",
    "tmt16plex",
    "itraq4plex",
    "itraq8plex",
}


def validate_advanced_modified_peptide_conflicts(
    peptide: ParsedModifiedPeptide,
) -> ModifiedPeptideConflictReport:
    """Refuse known mutually exclusive terminal/residue/isotope label combinations."""
    issues: list[ModifiedPeptideConflictIssue] = []

    n_terminal = [
        modification
        for modification in peptide.modifications
        if modification.site
        in {ModificationPosition.PEPTIDE_N_TERM, ModificationPosition.PROTEIN_N_TERM}
    ]
    c_terminal = [
        modification
        for modification in peptide.modifications
        if modification.site
        in {ModificationPosition.PEPTIDE_C_TERM, ModificationPosition.PROTEIN_C_TERM}
    ]
    if len(n_terminal) > 1:
        issues.append(
            ModifiedPeptideConflictIssue(
                code="multiple_n_terminal_modifications",
                message="multiple N-terminal modifications were assigned to one peptide hypothesis",
                involved_modifications=tuple(mod.name for mod in n_terminal),
            )
        )
    if len(c_terminal) > 1:
        issues.append(
            ModifiedPeptideConflictIssue(
                code="multiple_c_terminal_modifications",
                message="multiple C-terminal modifications were assigned to one peptide hypothesis",
                involved_modifications=tuple(mod.name for mod in c_terminal),
            )
        )

    assignments_by_site = defaultdict(list)
    for modification in peptide.modifications:
        site_key = (
            modification.site.value,
            modification.site_index,
            modification.residue,
        )
        assignments_by_site[site_key].append(modification)
    for site_modifications in assignments_by_site.values():
        if len(site_modifications) < 2:
            continue
        normalized = {
            modification.name.strip().lower().replace(" ", "")
            for modification in site_modifications
        }
        if len(normalized.intersection(_TERMINAL_LABEL_TOKENS)) > 1:
            issues.append(
                ModifiedPeptideConflictIssue(
                    code="terminal_label_collision",
                    message="multiple terminal label chemistries are assigned to the same site",
                    involved_modifications=tuple(
                        modification.name for modification in site_modifications
                    ),
                )
            )

    return ModifiedPeptideConflictReport(valid=not issues, issues=tuple(issues))
