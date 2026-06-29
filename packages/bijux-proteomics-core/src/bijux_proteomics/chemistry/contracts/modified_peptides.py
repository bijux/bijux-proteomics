# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Modified-peptide parsing, localization, and export owners."""

from __future__ import annotations

import json
from pathlib import Path
import re

from bijux_proteomics.chemistry.amino_acid_mass import _CANONICAL_RESIDUES
from bijux_proteomics.chemistry.contracts.models import (
    AppliedModification,
    IsotopicLabelingPolicy,
    ModificationLocalizationAdvisory,
    ModificationLocalizationCandidate,
    ModificationLocalizationState,
    ModificationPosition,
    ModificationProvenance,
    ModificationRegistryDocument,
    ModificationSiteValidationIssue,
    ModificationSiteValidationReport,
    ModifiedPeptideExportRecord,
    NeutralLoss,
    ParsedModifiedPeptide,
    StaticModification,
    VariableModification,
    VariableModificationEnumerationEntry,
    VariableModificationEnumerationReport,
    _RESIDUE_TOKEN_RE,
)
from bijux_proteomics.chemistry.contracts.registry_access import (
    get_modification,
    modification_registry,
    registry_lookup,
    resolve_modification_definition,
)

_DELTA_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")


def _format_mass_delta(delta: float) -> str:
    rendered = f"{delta:+.6f}".rstrip("0").rstrip(".")
    return rendered if "." in rendered else f"{rendered}.0"


def _build_applied_modification(
    *,
    token: str,
    site: ModificationPosition,
    site_index: int | None,
    sequence: str,
    registry: ModificationRegistryDocument | None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
    labeling_policy: IsotopicLabelingPolicy | None = None,
) -> AppliedModification:
    stripped_token = token.strip()
    definition = None
    if not _DELTA_TOKEN_RE.fullmatch(stripped_token):
        definition = resolve_modification_definition(
            token=stripped_token,
            site=site,
            residue=sequence[site_index - 1]
            if site is ModificationPosition.ANYWHERE and site_index is not None
            else None,
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
            registry=registry,
        )
    _validate_isotopic_label_policy(definition, labeling_policy=labeling_policy)
    residue = (
        sequence[site_index - 1]
        if site is ModificationPosition.ANYWHERE and site_index is not None
        else None
    )
    if definition is None:
        name, mono, average, losses, controlled_id, source = _resolve_token(
            stripped_token,
            registry=registry,
        )
    else:
        name = definition.name
        mono = definition.mass_delta_monoisotopic
        average = definition.mass_delta_average
        losses = definition.neutral_losses
        controlled_id = definition.controlled_id
        source = "registry"
    return AppliedModification(
        name=name,
        token=definition.name if definition is not None else _format_mass_delta(mono),
        site=site,
        site_index=site_index,
        residue=residue,
        mass_delta_monoisotopic=mono,
        mass_delta_average=average,
        neutral_losses=losses,
        controlled_id=controlled_id,
        source=source,
        provenance=_build_modification_provenance(
            token=stripped_token,
            source=source,
            resolved_name=name,
            definition=definition,
            controlled_id=controlled_id,
        ),
    )


def _candidate_definition_for_delta(
    *,
    delta: float,
    site: ModificationPosition,
    residue: str | None,
    registry: ModificationRegistryDocument | None,
    tolerance: float = 1e-6,
) -> StaticModification | VariableModification | None:
    for definition in registry_lookup(registry).values():
        if abs(definition.mass_delta_monoisotopic - delta) > tolerance:
            continue
        if definition.position is not site:
            continue
        if (
            site is ModificationPosition.ANYWHERE
            and residue is not None
            and definition.residues
            and residue not in definition.residues
        ):
            continue
        return definition
    return None


def _build_modification_provenance(
    *,
    token: str,
    source: str,
    resolved_name: str,
    definition: StaticModification | VariableModification | None,
    controlled_id: str | None,
) -> ModificationProvenance:
    if definition is not None:
        return ModificationProvenance(
            source=source,
            assignment_token=token,
            rule_path=(
                "modification_registry",
                definition.application,
                definition.name,
            ),
            resolved_name=resolved_name,
            controlled_id=controlled_id,
        )
    return ModificationProvenance(
        source=source,
        assignment_token=token,
        rule_path=("explicit_delta", _format_mass_delta(float(token))),
        resolved_name=resolved_name,
        controlled_id=controlled_id,
    )


def _validate_isotopic_label_policy(
    definition: StaticModification | VariableModification | None,
    *,
    labeling_policy: IsotopicLabelingPolicy | None,
) -> None:
    if definition is None or definition.isotopic_label_family is None:
        return
    if labeling_policy is None or not labeling_policy.allow_isotopic_labels:
        raise ValueError(
            f"isotopic label modification {definition.name!r} requires an explicit labeling policy"
        )
    if (
        labeling_policy.allowed_label_families
        and definition.isotopic_label_family
        not in labeling_policy.allowed_label_families
    ):
        raise ValueError(
            f"isotopic label family {definition.isotopic_label_family!r} is not allowed by the active labeling policy"
        )


def _coerce_sequence(peptide: str | ParsedModifiedPeptide) -> str:
    sequence = (
        peptide.sequence if isinstance(peptide, ParsedModifiedPeptide) else peptide
    )
    normalized = sequence.strip().upper()
    if not _RESIDUE_TOKEN_RE.fullmatch(normalized):
        raise ValueError(
            "peptide sequence must use canonical uppercase amino-acid symbols"
        )
    return normalized


def _ensure_parsed_peptide(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ParsedModifiedPeptide:
    if isinstance(peptide, ParsedModifiedPeptide):
        return peptide
    if "[" in peptide:
        return parse_modified_peptide(peptide, registry=registry)
    normalized = _coerce_sequence(peptide)
    return ParsedModifiedPeptide(
        sequence=normalized,
        modifications=(),
        at_protein_n_term=False,
        at_protein_c_term=False,
        canonical_notation=normalized,
    )


def _normalize_terminal_token(
    token: str,
    *,
    default_site: ModificationPosition,
) -> tuple[str, ModificationPosition]:
    name, separator, site_token = token.partition("@")
    if not separator:
        return token, default_site
    site_label = site_token.strip().lower()
    if site_label in {"protein-n-term", "protein_n_term", "protein-nterm"}:
        return name, ModificationPosition.PROTEIN_N_TERM
    if site_label in {"protein-c-term", "protein_c_term", "protein-cterm"}:
        return name, ModificationPosition.PROTEIN_C_TERM
    raise ValueError(f"unsupported terminal modification site {site_token!r}")


def build_modification_localization_advisory(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ModificationLocalizationAdvisory:
    """Emit an advisory-only localization summary until scored localization exists."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    mapping = registry_lookup(registry)
    try:
        canonical_notation = canonicalize_modified_peptide(parsed, registry=registry)
    except ValueError:
        canonical_notation = parsed.canonical_notation
    candidates: list[ModificationLocalizationCandidate] = []
    for modification in parsed.modifications:
        residue_scope: tuple[str, ...] = ()
        candidate_site_indices: tuple[int, ...] = ()
        if modification.source == "registry":
            definition = mapping.get(modification.name.strip().lower())
            if definition is not None:
                residue_scope = definition.residues
                if definition.position is ModificationPosition.ANYWHERE:
                    candidate_site_indices = tuple(
                        index
                        for index, residue in enumerate(parsed.sequence, start=1)
                        if residue in definition.residues
                    )
        elif modification.residue is not None and modification.site_index is not None:
            residue_scope = (modification.residue,)
            candidate_site_indices = tuple(
                index
                for index, residue in enumerate(parsed.sequence, start=1)
                if residue == modification.residue
            )

        candidates.append(
            ModificationLocalizationCandidate(
                modification_name=modification.name,
                assigned_site=modification.site,
                assigned_site_index=modification.site_index,
                candidate_site_indices=candidate_site_indices,
                residue_scope=residue_scope,
                localization_state=_classify_modification_localization_state(
                    modification=modification,
                    candidate_site_indices=candidate_site_indices,
                ),
                ambiguous=len(candidate_site_indices) > 1,
            )
        )
    return ModificationLocalizationAdvisory(
        canonical_notation=canonical_notation,
        note="localization is advisory only; site scores and probability models are not implemented yet",
        candidates=tuple(candidates),
    )


def _classify_modification_localization_state(
    *,
    modification: AppliedModification,
    candidate_site_indices: tuple[int, ...],
) -> ModificationLocalizationState:
    if modification.site is not ModificationPosition.ANYWHERE:
        return ModificationLocalizationState.LOCALIZED
    if not candidate_site_indices:
        return (
            ModificationLocalizationState.CONFLICTING
            if modification.site_index is not None
            else ModificationLocalizationState.UNSUPPORTED
        )
    if modification.site_index is None:
        return ModificationLocalizationState.UNLOCALIZED
    if modification.site_index not in candidate_site_indices:
        return ModificationLocalizationState.CONFLICTING
    if len(candidate_site_indices) > 1:
        return ModificationLocalizationState.AMBIGUOUS
    return ModificationLocalizationState.LOCALIZED


def enumerate_variable_modifications(
    peptide: str | ParsedModifiedPeptide,
    *,
    variable_modifications: tuple[VariableModification, ...] = (),
    registry: ModificationRegistryDocument | None = None,
    labeling_policy: IsotopicLabelingPolicy | None = None,
    max_variants: int = 128,
) -> VariableModificationEnumerationReport:
    """Enumerate deterministic modified-peptide variants within a hard bound."""
    if max_variants < 1:
        raise ValueError("max_variants must be at least 1")
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    definitions = (
        variable_modifications
        if variable_modifications
        else (registry or modification_registry()).variable_modifications
    )
    candidate_groups = [
        _enumeration_candidates_for_definition(
            parsed,
            definition=definition,
            registry=registry,
            labeling_policy=labeling_policy,
        )
        for definition in definitions
    ]
    base_site_keys: set[tuple[str, int | None]] = set()
    for modification in parsed.modifications:
        site_key = _physical_site_key(modification)
        if site_key is not None:
            base_site_keys.add(site_key)
    variants: list[VariableModificationEnumerationEntry] = []
    truncated = False

    def visit(
        index: int,
        selected: list[AppliedModification],
        occupied_site_keys: set[tuple[str, int | None]],
    ) -> None:
        nonlocal truncated
        if truncated:
            return
        if index == len(candidate_groups):
            combined = tuple(
                sorted(
                    (*parsed.modifications, *selected),
                    key=lambda modification: (
                        0
                        if modification.site
                        in {
                            ModificationPosition.PEPTIDE_N_TERM,
                            ModificationPosition.PROTEIN_N_TERM,
                        }
                        else 1,
                        modification.site_index or 0,
                        2
                        if modification.site
                        in {
                            ModificationPosition.PEPTIDE_C_TERM,
                            ModificationPosition.PROTEIN_C_TERM,
                        }
                        else 1,
                        modification.token,
                    ),
                )
            )
            variants.append(
                VariableModificationEnumerationEntry(
                    canonical_notation=_render_modified_peptide(
                        parsed.sequence,
                        combined,
                    ),
                    modification_count=len(combined),
                    modifications=combined,
                )
            )
            if len(variants) >= max_variants:
                truncated = True
            return

        definition, candidates = candidate_groups[index]
        definition_limit = definition.max_occurrences or len(candidates)
        candidate_choices: list[tuple[AppliedModification, ...]] = [()]
        for count in range(1, min(definition_limit, len(candidates)) + 1):
            candidate_choices.extend(combinations(candidates, count))

        for choice in candidate_choices:
            choice_site_keys = {
                _physical_site_key(modification) for modification in choice
            }
            if None in choice_site_keys:
                continue
            typed_choice_site_keys: set[tuple[str, int | None]] = {
                site_key for site_key in choice_site_keys if site_key is not None
            }
            if occupied_site_keys & typed_choice_site_keys:
                continue
            visit(
                index + 1,
                [*selected, *choice],
                occupied_site_keys | typed_choice_site_keys,
            )

    from itertools import combinations

    visit(0, [], set(base_site_keys))
    return VariableModificationEnumerationReport(
        sequence=parsed.sequence,
        at_protein_n_term=parsed.at_protein_n_term,
        at_protein_c_term=parsed.at_protein_c_term,
        base_modification_count=len(parsed.modifications),
        candidate_site_count=sum(
            len(candidates) for _definition, candidates in candidate_groups
        ),
        generated_variant_count=len(variants),
        max_variants=max_variants,
        truncated=truncated,
        variants=tuple(variants),
    )


def _resolve_token(
    token: str,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> tuple[str, float, float, tuple[NeutralLoss, ...], str | None, str]:
    normalized = token.strip()
    if _DELTA_TOKEN_RE.fullmatch(normalized):
        delta = float(normalized)
        return (
            f"delta:{_format_mass_delta(delta)}",
            delta,
            delta,
            (),
            None,
            "delta",
        )

    definition = get_modification(normalized, registry=registry)
    return (
        definition.name,
        definition.mass_delta_monoisotopic,
        definition.mass_delta_average,
        definition.neutral_losses,
        definition.controlled_id,
        "registry",
    )


def _validate_definition_site(
    *,
    definition: StaticModification | VariableModification | None,
    sequence: str,
    site: ModificationPosition,
    site_index: int | None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
) -> str | None:
    if definition is None:
        return sequence[site_index - 1] if site_index is not None else None
    allowed_sites = {definition.position}
    if definition.position is ModificationPosition.PEPTIDE_N_TERM:
        allowed_sites.add(ModificationPosition.PROTEIN_N_TERM)
    if definition.position is ModificationPosition.PEPTIDE_C_TERM:
        allowed_sites.add(ModificationPosition.PROTEIN_C_TERM)
    if site not in allowed_sites:
        raise ValueError(
            f"modification {definition.name!r} requires site {definition.position.value}, got {site.value}"
        )
    if site is ModificationPosition.ANYWHERE:
        if site_index is None:
            raise ValueError(
                f"modification {definition.name!r} requires a residue site index"
            )
        residue = sequence[site_index - 1]
        if definition.residues and residue not in definition.residues:
            allowed = ",".join(definition.residues)
            raise ValueError(
                f"modification {definition.name!r} is not valid on residue {residue} at position {site_index}; expected one of {allowed}"
            )
        return residue
    if site is ModificationPosition.PROTEIN_N_TERM and not at_protein_n_term:
        raise ValueError(
            f"modification {definition.name!r} requires a peptide at the protein N-terminus"
        )
    if site is ModificationPosition.PROTEIN_C_TERM and not at_protein_c_term:
        raise ValueError(
            f"modification {definition.name!r} requires a peptide at the protein C-terminus"
        )
    return None


def _enumeration_candidates_for_definition(
    peptide: ParsedModifiedPeptide,
    *,
    definition: VariableModification,
    registry: ModificationRegistryDocument | None,
    labeling_policy: IsotopicLabelingPolicy | None,
) -> tuple[VariableModification, tuple[AppliedModification, ...]]:
    sequence = peptide.sequence
    candidates: list[AppliedModification] = []
    if definition.position is ModificationPosition.ANYWHERE:
        for site_index, residue in enumerate(sequence, start=1):
            if residue not in definition.residues:
                continue
            candidates.append(
                _build_applied_modification(
                    token=definition.name,
                    site=ModificationPosition.ANYWHERE,
                    site_index=site_index,
                    sequence=sequence,
                    registry=registry,
                    at_protein_n_term=peptide.at_protein_n_term,
                    at_protein_c_term=peptide.at_protein_c_term,
                    labeling_policy=labeling_policy,
                )
            )
    elif definition.position is ModificationPosition.PEPTIDE_N_TERM:
        candidates.append(
            _build_applied_modification(
                token=definition.name,
                site=ModificationPosition.PEPTIDE_N_TERM,
                site_index=None,
                sequence=sequence,
                registry=registry,
                at_protein_n_term=peptide.at_protein_n_term,
                at_protein_c_term=peptide.at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
    elif definition.position is ModificationPosition.PEPTIDE_C_TERM:
        candidates.append(
            _build_applied_modification(
                token=definition.name,
                site=ModificationPosition.PEPTIDE_C_TERM,
                site_index=None,
                sequence=sequence,
                registry=registry,
                at_protein_n_term=peptide.at_protein_n_term,
                at_protein_c_term=peptide.at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
    elif definition.position is ModificationPosition.PROTEIN_N_TERM:
        if peptide.at_protein_n_term:
            candidates.append(
                _build_applied_modification(
                    token=definition.name,
                    site=ModificationPosition.PROTEIN_N_TERM,
                    site_index=None,
                    sequence=sequence,
                    registry=registry,
                    at_protein_n_term=peptide.at_protein_n_term,
                    at_protein_c_term=peptide.at_protein_c_term,
                    labeling_policy=labeling_policy,
                )
            )
    elif (
        definition.position is ModificationPosition.PROTEIN_C_TERM
        and peptide.at_protein_c_term
    ):
        candidates.append(
            _build_applied_modification(
                token=definition.name,
                site=ModificationPosition.PROTEIN_C_TERM,
                site_index=None,
                sequence=sequence,
                registry=registry,
                at_protein_n_term=peptide.at_protein_n_term,
                at_protein_c_term=peptide.at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
    return definition, tuple(candidates)


def _physical_site_key(
    modification: AppliedModification,
) -> tuple[str, int | None] | None:
    if modification.site is ModificationPosition.ANYWHERE:
        return ("residue", modification.site_index)
    if modification.site in {
        ModificationPosition.PEPTIDE_N_TERM,
        ModificationPosition.PROTEIN_N_TERM,
    }:
        return ("n_term", None)
    if modification.site in {
        ModificationPosition.PEPTIDE_C_TERM,
        ModificationPosition.PROTEIN_C_TERM,
    }:
        return ("c_term", None)
    return None


def _raise_on_impossible_modification_combination(
    modifications: tuple[AppliedModification, ...],
) -> None:
    by_site: dict[tuple[str, int | None], list[AppliedModification]] = {}
    for modification in modifications:
        site_key = _physical_site_key(modification)
        if site_key is None:
            continue
        by_site.setdefault(site_key, []).append(modification)

    conflicting_sites = [
        (site_key, site_modifications)
        for site_key, site_modifications in by_site.items()
        if len(site_modifications) > 1
    ]
    if not conflicting_sites:
        return

    site_key, site_modifications = conflicting_sites[0]
    site_label = (
        f"residue {site_key[1]}"
        if site_key[0] == "residue"
        else "peptide N-terminus"
        if site_key[0] == "n_term"
        else "peptide C-terminus"
    )
    tokens = ", ".join(modification.token for modification in site_modifications)
    raise ValueError(
        f"chemically incompatible modifications occupy the same physical site ({site_label}): {tokens}"
    )


def parse_modified_peptide(
    notation: str,
    *,
    registry: ModificationRegistryDocument | None = None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
    labeling_policy: IsotopicLabelingPolicy | None = None,
) -> ParsedModifiedPeptide:
    """Parse modified peptide bracket notation into a stable contract."""
    text = notation.strip()
    modifications: list[AppliedModification] = []

    index = 0
    residues: list[str] = []

    if text.startswith("["):
        close = text.find("]")
        if close == -1 or close + 1 >= len(text) or text[close + 1] != "-":
            raise ValueError(
                "N-terminal modifications must use [token]-PEPTIDE notation"
            )
        token = text[1:close]
        token, parsed_site = _normalize_terminal_token(
            token,
            default_site=ModificationPosition.PEPTIDE_N_TERM,
        )
        modifications.append(
            _build_applied_modification(
                token=token,
                site=parsed_site,
                site_index=None,
                sequence="",
                registry=registry,
                at_protein_n_term=at_protein_n_term,
                at_protein_c_term=at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
        index = close + 2

    while index < len(text):
        character = text[index]
        if character == "-":
            break
        if character not in _CANONICAL_RESIDUES:
            raise ValueError(f"invalid peptide notation character {character!r}")
        residues.append(character)
        index += 1
        if index < len(text) and text[index] == "[":
            close = text.find("]", index)
            if close == -1:
                raise ValueError("unterminated modification token")
            token = text[index + 1 : close]
            sequence = "".join(residues)
            modifications.append(
                _build_applied_modification(
                    token=token,
                    site=ModificationPosition.ANYWHERE,
                    site_index=len(sequence),
                    sequence=sequence,
                    registry=registry,
                    at_protein_n_term=at_protein_n_term,
                    at_protein_c_term=at_protein_c_term,
                    labeling_policy=labeling_policy,
                )
            )
            index = close + 1

    sequence = "".join(residues)
    if not sequence:
        raise ValueError("modified peptide notation must contain at least one residue")

    if index < len(text):
        if not text[index:].startswith("-[") or not text.endswith("]"):
            raise ValueError(
                "C-terminal modifications must use PEPTIDE-[token] notation"
            )
        token = text[index + 2 : -1]
        token, parsed_site = _normalize_terminal_token(
            token,
            default_site=ModificationPosition.PEPTIDE_C_TERM,
        )
        modifications.append(
            _build_applied_modification(
                token=token,
                site=parsed_site,
                site_index=None,
                sequence=sequence,
                registry=registry,
                at_protein_n_term=at_protein_n_term,
                at_protein_c_term=at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )

    _raise_on_impossible_modification_combination(tuple(modifications))
    return ParsedModifiedPeptide(
        sequence=sequence,
        modifications=tuple(modifications),
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
        canonical_notation=_render_modified_peptide(sequence, tuple(modifications)),
    )


def build_modified_peptide(
    sequence: str,
    *,
    assignments: tuple[str, ...] = (),
    registry: ModificationRegistryDocument | None = None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
    labeling_policy: IsotopicLabelingPolicy | None = None,
) -> ParsedModifiedPeptide:
    """Build a modified peptide from site-assignment strings."""
    normalized = _coerce_sequence(sequence)
    modifications: list[AppliedModification] = []
    for assignment in assignments:
        token, separator, site_token = assignment.partition("@")
        if not separator:
            raise ValueError(
                "modification assignments must use token@site syntax such as Oxidation@3 or Acetyl@n-term"
            )
        site_label = site_token.strip().lower()
        if site_label in {"n-term", "nterm", "peptide_n_term"}:
            site = ModificationPosition.PEPTIDE_N_TERM
            site_index = None
        elif site_label in {"protein-n-term", "protein_n_term", "protein-nterm"}:
            site = ModificationPosition.PROTEIN_N_TERM
            site_index = None
        elif site_label in {"c-term", "cterm", "peptide_c_term"}:
            site = ModificationPosition.PEPTIDE_C_TERM
            site_index = None
        elif site_label in {"protein-c-term", "protein_c_term", "protein-cterm"}:
            site = ModificationPosition.PROTEIN_C_TERM
            site_index = None
        else:
            try:
                site_index = int(site_label)
            except ValueError as exc:
                raise ValueError(f"invalid modification site {site_token!r}") from exc
            if site_index < 1 or site_index > len(normalized):
                raise ValueError(
                    f"modification site {site_index} is outside peptide length {len(normalized)}"
                )
            site = ModificationPosition.ANYWHERE
        modifications.append(
            _build_applied_modification(
                token=token,
                site=site,
                site_index=site_index,
                sequence=normalized
                if site is ModificationPosition.ANYWHERE
                else normalized,
                registry=registry,
                at_protein_n_term=at_protein_n_term,
                at_protein_c_term=at_protein_c_term,
                labeling_policy=labeling_policy,
            )
        )
    _raise_on_impossible_modification_combination(tuple(modifications))
    ordered = tuple(
        sorted(
            modifications,
            key=lambda modification: (
                0 if modification.site is ModificationPosition.PEPTIDE_N_TERM else 1,
                modification.site_index or 0,
                2 if modification.site is ModificationPosition.PEPTIDE_C_TERM else 1,
                modification.token,
            ),
        )
    )
    return ParsedModifiedPeptide(
        sequence=normalized,
        modifications=ordered,
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
        canonical_notation=_render_modified_peptide(normalized, ordered),
    )


def canonicalize_modified_peptide(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> str:
    """Return a stable canonical notation for one modified peptide."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    canonicalized: list[AppliedModification] = []
    for modification in parsed.modifications:
        if modification.source == "delta":
            definition = _candidate_definition_for_delta(
                delta=modification.mass_delta_monoisotopic,
                site=modification.site,
                residue=modification.residue,
                registry=registry,
            )
            if definition is not None:
                canonicalized.append(
                    modification.model_copy(
                        update={
                            "name": definition.name,
                            "token": definition.name,
                            "controlled_id": definition.controlled_id,
                            "neutral_losses": definition.neutral_losses,
                        }
                    )
                )
                continue
        elif modification.source == "registry":
            canonicalized.append(
                modification.model_copy(update={"token": modification.name})
            )
            continue
        canonicalized.append(
            modification.model_copy(
                update={
                    "token": _format_mass_delta(modification.mass_delta_monoisotopic)
                }
            )
        )
    ordered = tuple(
        sorted(
            canonicalized,
            key=lambda modification: (
                0 if modification.site is ModificationPosition.PEPTIDE_N_TERM else 1,
                modification.site_index or 0,
                2 if modification.site is ModificationPosition.PEPTIDE_C_TERM else 1,
                modification.token,
            ),
        )
    )
    return _render_modified_peptide(parsed.sequence, ordered)


def build_modified_peptide_export_record(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ModifiedPeptideExportRecord:
    """Build one stable export record for a canonical modified peptide."""
    parsed = _ensure_parsed_peptide(peptide, registry=registry)
    canonical = canonicalize_modified_peptide(parsed, registry=registry)
    ordered = tuple(
        sorted(
            parsed.modifications,
            key=lambda modification: (
                0
                if modification.site
                in {
                    ModificationPosition.PEPTIDE_N_TERM,
                    ModificationPosition.PROTEIN_N_TERM,
                }
                else 1,
                modification.site_index or 0,
                2
                if modification.site
                in {
                    ModificationPosition.PEPTIDE_C_TERM,
                    ModificationPosition.PROTEIN_C_TERM,
                }
                else 1,
                modification.token,
            ),
        )
    )
    return ModifiedPeptideExportRecord(
        canonical_notation=canonical,
        sequence=parsed.sequence,
        modification_count=len(ordered),
        modification_sites=tuple(
            _render_modification_site(modification) for modification in ordered
        ),
        modifications=ordered,
    )


def export_modified_peptides_jsonl(
    peptides: tuple[str | ParsedModifiedPeptide, ...],
    path: Path,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> Path:
    """Write stable JSONL export rows for canonical modified peptides."""
    rows = [
        build_modified_peptide_export_record(peptide, registry=registry).to_dict()
        for peptide in peptides
    ]
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n")
    return path


def export_modified_peptides_tsv(
    peptides: tuple[str | ParsedModifiedPeptide, ...],
    path: Path,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> Path:
    """Write stable TSV export rows for canonical modified peptides."""
    header = "\t".join(
        [
            "canonical_notation",
            "sequence",
            "modification_count",
            "modification_sites",
        ]
    )
    lines = [header]
    for peptide in peptides:
        record = build_modified_peptide_export_record(peptide, registry=registry)
        lines.append(
            "\t".join(
                [
                    record.canonical_notation,
                    record.sequence,
                    str(record.modification_count),
                    ";".join(record.modification_sites),
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n")
    return path


def validate_modified_peptide_sites(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> ModificationSiteValidationReport:
    """Validate modified peptide site assignments into a structured report."""
    try:
        parsed = _ensure_parsed_peptide(peptide, registry=registry)
    except ValueError as exc:
        text = (
            peptide.sequence
            if isinstance(peptide, ParsedModifiedPeptide)
            else str(peptide)
        )
        sequence = "".join(
            character for character in text.upper() if character.isalpha()
        )
        return ModificationSiteValidationReport(
            valid=False,
            sequence=sequence or "UNKNOWN",
            issues=(
                ModificationSiteValidationIssue(
                    code="invalid_modification_site",
                    message=str(exc),
                    site=ModificationPosition.ANYWHERE,
                ),
            ),
        )
    return ModificationSiteValidationReport(
        valid=True,
        sequence=parsed.sequence,
        canonical_notation=canonicalize_modified_peptide(parsed, registry=registry),
        issues=(),
    )


def _render_modified_peptide(
    sequence: str,
    modifications: tuple[AppliedModification, ...],
) -> str:
    tokens_by_index: dict[int, list[str]] = {}
    n_term_tokens: list[str] = []
    c_term_tokens: list[str] = []
    for modification in modifications:
        token = _render_modification_token(modification)
        if modification.site in {
            ModificationPosition.PEPTIDE_N_TERM,
            ModificationPosition.PROTEIN_N_TERM,
        }:
            n_term_tokens.append(f"[{token}]")
        elif modification.site in {
            ModificationPosition.PEPTIDE_C_TERM,
            ModificationPosition.PROTEIN_C_TERM,
        }:
            c_term_tokens.append(f"[{token}]")
        else:
            site_index = modification.site_index
            if site_index is None:
                raise ValueError(
                    "residue modification is missing a required site index"
                )
            tokens_by_index.setdefault(site_index, []).append(f"[{token}]")

    rendered = "".join(n_term_tokens)
    if n_term_tokens:
        rendered += "-"
    for index, residue in enumerate(sequence, start=1):
        rendered += residue
        for token in tokens_by_index.get(index, ()):
            rendered += token
    if c_term_tokens:
        rendered += "-" + "".join(c_term_tokens)
    return rendered


def _render_modification_token(modification: AppliedModification) -> str:
    if modification.site is ModificationPosition.PROTEIN_N_TERM:
        return f"{modification.token}@protein-n-term"
    if modification.site is ModificationPosition.PROTEIN_C_TERM:
        return f"{modification.token}@protein-c-term"
    return modification.token


def _render_modification_site(modification: AppliedModification) -> str:
    if modification.site is ModificationPosition.ANYWHERE:
        return str(modification.site_index)
    if modification.site is ModificationPosition.PEPTIDE_N_TERM:
        return "peptide_n_term"
    if modification.site is ModificationPosition.PEPTIDE_C_TERM:
        return "peptide_c_term"
    if modification.site is ModificationPosition.PROTEIN_N_TERM:
        return "protein_n_term"
    return "protein_c_term"



__all__ = [
    "build_modified_peptide",
    "build_modified_peptide_export_record",
    "build_modification_localization_advisory",
    "canonicalize_modified_peptide",
    "enumerate_variable_modifications",
    "export_modified_peptides_jsonl",
    "export_modified_peptides_tsv",
    "parse_modified_peptide",
    "validate_modified_peptide_sites",
]
