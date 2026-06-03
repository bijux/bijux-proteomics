# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned registry engine for peptide modification definitions and rejection logic."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
import re

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.chemistry.amino_acid_mass import _CANONICAL_RESIDUES
from bijux_proteomics.chemistry.contracts import (
    ModificationPosition,
    ModificationRegistryDocument,
    ModificationRegistryValidationIssue,
    ModificationRegistryValidationReport,
    NeutralLoss,
    StaticModification,
    VariableModification,
    _BaseModification,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel

_PHOSPHORIC_ACID_MONOISOTOPIC_MASS = 97.976896
_PHOSPHORIC_ACID_AVERAGE_MASS = 97.9952
_DELTA_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")


class ModificationRegistryResolutionSource(StrEnum):
    """Where a resolved modification definition came from."""

    BUILTIN = "builtin"
    REGISTRY = "registry"
    UNKNOWN = "unknown"


class ModificationRegistryResolutionMode(StrEnum):
    """How one modification definition was matched."""

    NAME = "name"
    CONTROLLED_ID = "controlled_id"
    MASS_DELTA = "mass_delta"


class ModificationRegistryRejection(JsonModel):
    """One explicit reason a modification query could not be accepted."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ModificationRegistryResolutionReport(JsonModel):
    """Resolve-or-reject output for one modification query."""

    model_config = ConfigDict(extra="forbid")

    matched: bool
    accepted: bool
    source: ModificationRegistryResolutionSource
    match_mode: ModificationRegistryResolutionMode | None = None
    query_token: str | None = None
    query_controlled_id: str | None = None
    query_mass_delta_monoisotopic: float | None = None
    query_site: ModificationPosition | None = None
    query_residue: str | None = None
    at_protein_n_term: bool = False
    at_protein_c_term: bool = False
    modification_name: str | None = None
    controlled_id: str | None = None
    application: str | None = None
    position: ModificationPosition | None = None
    residues: tuple[str, ...] = Field(default_factory=tuple)
    mass_delta_monoisotopic: float | None = None
    mass_delta_average: float | None = None
    elemental_composition_delta: dict[str, int] = Field(default_factory=dict)
    neutral_losses: tuple[NeutralLoss, ...] = Field(default_factory=tuple)
    isotopic_label_family: str | None = None
    residue_allowed: bool | None = None
    rejection: ModificationRegistryRejection | None = None

    @field_validator("query_residue")
    @classmethod
    def _normalize_query_residue(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in _CANONICAL_RESIDUES:
            raise ValueError(f"invalid residue {value!r}")
        return normalized


def validate_modification_registry(
    registry: ModificationRegistryDocument,
) -> ModificationRegistryValidationReport:
    """Validate duplicate and conflicting registry definitions."""
    issues: list[ModificationRegistryValidationIssue] = []
    by_name: dict[str, _BaseModification] = {}
    by_controlled_id: dict[str, _BaseModification] = {}
    for modification in (
        *registry.static_modifications,
        *registry.variable_modifications,
    ):
        normalized_name = modification.name.strip().lower()
        previous = by_name.get(normalized_name)
        if previous is not None:
            conflict_code = (
                "duplicate_modification_name"
                if _registry_validation_signature(previous)
                == _registry_validation_signature(modification)
                else "conflicting_modification_name"
            )
            issues.append(
                ModificationRegistryValidationIssue(
                    code=conflict_code,
                    message=(
                        f"modification {modification.name!r} is defined more than once"
                        if conflict_code == "duplicate_modification_name"
                        else f"modification {modification.name!r} has conflicting definitions"
                    ),
                    modification_name=modification.name,
                    controlled_id=modification.controlled_id,
                )
            )
        else:
            by_name[normalized_name] = modification

        if modification.controlled_id is None:
            continue
        previous_controlled = by_controlled_id.get(modification.controlled_id)
        if previous_controlled is not None and (
            _registry_validation_signature(previous_controlled)
            != _registry_validation_signature(modification)
        ):
            issues.append(
                ModificationRegistryValidationIssue(
                    code="conflicting_controlled_id",
                    message=(
                        f"controlled modification id {modification.controlled_id!r} maps "
                        "to conflicting registry definitions"
                    ),
                    modification_name=modification.name,
                    controlled_id=modification.controlled_id,
                )
            )
        else:
            by_controlled_id[modification.controlled_id] = modification

    return ModificationRegistryValidationReport(
        valid=not issues,
        issues=tuple(issues),
    )


def build_modification_registry(
    *,
    static_modifications: tuple[StaticModification, ...] = (),
    variable_modifications: tuple[VariableModification, ...] = (),
) -> ModificationRegistryDocument:
    """Build a stable user-supplied modification registry document."""
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="peptide_modification_registry",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    registry = ModificationRegistryDocument(
        document_schema=schema,
        static_modifications=static_modifications,
        variable_modifications=variable_modifications,
    )
    _raise_on_invalid_modification_registry(registry)
    payload = registry.to_dict()
    return registry.model_copy(
        update={"document_schema": registry.document_schema.with_content_hash(payload)}
    )


def modification_registry() -> ModificationRegistryDocument:
    """Return the built-in peptide modification registry."""
    return _BUILTIN_REGISTRY.model_copy(deep=True)


def load_modification_registry(path: Path) -> ModificationRegistryDocument:
    """Load and validate a modification registry document from JSON."""
    registry = ModificationRegistryDocument.model_validate_json(path.read_text())
    _raise_on_invalid_modification_registry(registry)
    return registry


def get_modification(
    name: str,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> StaticModification | VariableModification:
    """Return one modification definition from the active registry."""
    report = resolve_modification(
        token=name,
        registry=registry,
    )
    if report.matched and report.accepted:
        return _definition_from_report(report)
    if report.rejection is None:
        raise ValueError(f"unknown modification {name!r}")
    raise ValueError(report.rejection.message)


def resolve_modification_definition(
    *,
    token: str | None = None,
    controlled_id: str | None = None,
    mass_delta_monoisotopic: float | None = None,
    site: ModificationPosition | None = None,
    residue: str | None = None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
    registry: ModificationRegistryDocument | None = None,
    tolerance: float = 1e-6,
) -> StaticModification | VariableModification:
    """Resolve one modification definition with full site context or raise."""
    report = resolve_modification(
        token=token,
        controlled_id=controlled_id,
        mass_delta_monoisotopic=mass_delta_monoisotopic,
        site=site,
        residue=residue,
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
        registry=registry,
        tolerance=tolerance,
    )
    if report.matched and report.accepted:
        return _definition_from_report(report)
    if report.rejection is None:
        query = token or controlled_id or f"{mass_delta_monoisotopic:+.6f}"
        raise ValueError(f"unknown modification {query!r}")
    raise ValueError(report.rejection.message)


def resolve_modification(
    *,
    token: str | None = None,
    controlled_id: str | None = None,
    mass_delta_monoisotopic: float | None = None,
    site: ModificationPosition | None = None,
    residue: str | None = None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
    registry: ModificationRegistryDocument | None = None,
    tolerance: float = 1e-6,
) -> ModificationRegistryResolutionReport:
    """Resolve one modification definition and reject site-incompatible queries explicitly."""
    normalized_token = token.strip() if token is not None else None
    normalized_controlled_id = (
        controlled_id.strip() if controlled_id is not None else None
    )
    normalized_residue = residue.strip().upper() if residue is not None else None
    if (
        normalized_token in (None, "")
        and normalized_controlled_id in (None, "")
        and mass_delta_monoisotopic is None
    ):
        raise ValueError(
            "modification resolution requires a token, controlled id, or monoisotopic mass delta"
        )
    if normalized_residue is not None and normalized_residue not in _CANONICAL_RESIDUES:
        raise ValueError(f"invalid residue {residue!r}")

    definition: StaticModification | VariableModification | None = None
    match_mode: ModificationRegistryResolutionMode | None = None
    rejection: ModificationRegistryRejection | None = None

    if normalized_controlled_id not in (None, ""):
        controlled_id_value = normalized_controlled_id
        assert controlled_id_value is not None
        definition = _lookup_by_controlled_id(controlled_id_value, registry=registry)
        match_mode = ModificationRegistryResolutionMode.CONTROLLED_ID
        if definition is None:
            rejection = ModificationRegistryRejection(
                code="unknown_controlled_id",
                message=f"unknown modification controlled id {controlled_id!r}",
            )
    elif normalized_token not in (None, ""):
        token_value = normalized_token
        assert token_value is not None
        definition = _lookup_by_token(
            token_value,
            site=site,
            residue=normalized_residue,
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
            registry=registry,
        )
        match_mode = ModificationRegistryResolutionMode.NAME
        if definition is None:
            rejection = ModificationRegistryRejection(
                code="unknown_modification",
                message=f"unknown modification {token!r}",
            )
    else:
        definition, rejection = _lookup_by_mass_delta(
            mass_delta_monoisotopic=mass_delta_monoisotopic,
            site=site,
            residue=normalized_residue,
            registry=registry,
            tolerance=tolerance,
        )
        match_mode = ModificationRegistryResolutionMode.MASS_DELTA

    if definition is None:
        return ModificationRegistryResolutionReport(
            matched=False,
            accepted=False,
            source=ModificationRegistryResolutionSource.UNKNOWN,
            match_mode=match_mode,
            query_token=normalized_token,
            query_controlled_id=normalized_controlled_id,
            query_mass_delta_monoisotopic=mass_delta_monoisotopic,
            query_site=site,
            query_residue=normalized_residue,
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
            rejection=rejection,
        )

    source = _classify_resolution_source(definition, registry=registry)
    compatibility_rejection = _site_compatibility_rejection(
        definition=definition,
        site=site,
        residue=normalized_residue,
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
    )
    return ModificationRegistryResolutionReport(
        matched=True,
        accepted=compatibility_rejection is None,
        source=source,
        match_mode=match_mode,
        query_token=normalized_token,
        query_controlled_id=normalized_controlled_id,
        query_mass_delta_monoisotopic=mass_delta_monoisotopic,
        query_site=site,
        query_residue=normalized_residue,
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
        modification_name=definition.name,
        controlled_id=definition.controlled_id,
        application="static"
        if isinstance(definition, StaticModification)
        else "variable",
        position=definition.position,
        residues=definition.residues,
        mass_delta_monoisotopic=definition.mass_delta_monoisotopic,
        mass_delta_average=definition.mass_delta_average,
        elemental_composition_delta=definition.elemental_composition_delta,
        neutral_losses=definition.neutral_losses,
        isotopic_label_family=definition.isotopic_label_family,
        residue_allowed=_residue_allowed(definition, normalized_residue),
        rejection=compatibility_rejection,
    )


def resolve_modification_site(
    *,
    definition: StaticModification | VariableModification | None,
    sequence: str,
    site: ModificationPosition,
    site_index: int | None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
) -> str | None:
    """Validate site compatibility for one resolved definition and return the resolved residue."""
    if definition is None:
        return sequence[site_index - 1] if site_index is not None else None
    residue = sequence[site_index - 1] if site_index is not None else None
    rejection = _site_compatibility_rejection(
        definition=definition,
        site=site,
        residue=residue,
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
        require_site_index=True,
        site_index=site_index,
    )
    if rejection is not None:
        raise ValueError(rejection.message)
    return residue


def _lookup_by_token(
    token: str,
    *,
    site: ModificationPosition | None,
    residue: str | None,
    at_protein_n_term: bool,
    at_protein_c_term: bool,
    registry: ModificationRegistryDocument | None,
) -> StaticModification | VariableModification | None:
    normalized = token.strip().lower()
    canonical_token = _MODIFICATION_TOKEN_ALIASES.get(normalized, normalized)
    mapping = _registry_lookup(registry)
    exact = mapping.get(normalized)
    if exact is None and canonical_token != normalized:
        exact = mapping.get(canonical_token)
    if site is None:
        return exact or _family_candidate(
            token=canonical_token,
            mapping=mapping,
            site=site,
            residue=residue,
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
        )
    if exact is not None:
        if _site_compatibility_rejection(
            definition=exact,
            site=site,
            residue=residue,
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
        ) is None:
            return exact
        family_definition = _family_candidate(
            token=canonical_token,
            mapping=mapping,
            site=site,
            residue=residue,
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
        )
        return family_definition or exact
    return _family_candidate(
        token=canonical_token,
        mapping=mapping,
        site=site,
        residue=residue,
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
    )


def _family_candidate(
    *,
    token: str,
    mapping: dict[str, StaticModification | VariableModification],
    site: ModificationPosition | None,
    residue: str | None,
    at_protein_n_term: bool,
    at_protein_c_term: bool,
) -> StaticModification | VariableModification | None:
    candidate_keys = _MODIFICATION_TOKEN_FAMILIES.get(token, ())
    compatible: list[StaticModification | VariableModification] = []
    for candidate_key in candidate_keys:
        definition = mapping.get(candidate_key)
        if definition is None:
            continue
        if site is None:
            compatible.append(definition)
            continue
        if _site_compatibility_rejection(
            definition=definition,
            site=site,
            residue=residue,
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
        ) is None:
            compatible.append(definition)
    if not compatible:
        return None
    if len(compatible) == 1:
        return compatible[0]
    if token in {definition.name.strip().lower() for definition in compatible}:
        for definition in compatible:
            if definition.name.strip().lower() == token:
                return definition
    return None


def _lookup_by_controlled_id(
    controlled_id: str,
    *,
    registry: ModificationRegistryDocument | None,
) -> StaticModification | VariableModification | None:
    return _registry_lookup(registry).get(controlled_id.strip().lower())


def _lookup_by_mass_delta(
    *,
    mass_delta_monoisotopic: float | None,
    site: ModificationPosition | None,
    residue: str | None,
    registry: ModificationRegistryDocument | None,
    tolerance: float,
) -> tuple[
    StaticModification | VariableModification | None,
    ModificationRegistryRejection | None,
]:
    if mass_delta_monoisotopic is None:
        return None, ModificationRegistryRejection(
            code="missing_mass_delta",
            message="modification mass-delta resolution requires a monoisotopic mass delta",
        )
    candidates = [
        definition
        for definition in _unique_registry_definitions(registry)
        if abs(definition.mass_delta_monoisotopic - mass_delta_monoisotopic) <= tolerance
    ]
    if site is not None:
        candidates = [
            definition
            for definition in candidates
            if site in _allowed_sites(definition)
        ]
    if residue is not None:
        residue_filtered = [
            definition
            for definition in candidates
            if definition.position is not ModificationPosition.ANYWHERE
            or not definition.residues
            or residue in definition.residues
        ]
        if residue_filtered:
            candidates = residue_filtered
    if not candidates:
        return None, ModificationRegistryRejection(
            code="unknown_mass_delta",
            message=(
                "no modification definition matches monoisotopic mass delta "
                f"{mass_delta_monoisotopic:+.6f}"
            ),
        )
    if len(candidates) > 1:
        names = ", ".join(sorted(definition.name for definition in candidates))
        return None, ModificationRegistryRejection(
            code="ambiguous_mass_delta",
            message=(
                "monoisotopic mass delta "
                f"{mass_delta_monoisotopic:+.6f} matches multiple modification definitions: {names}"
            ),
        )
    return candidates[0], None


def _allowed_sites(
    definition: StaticModification | VariableModification,
) -> set[ModificationPosition]:
    allowed = {definition.position}
    if definition.position is ModificationPosition.PEPTIDE_N_TERM:
        allowed.add(ModificationPosition.PROTEIN_N_TERM)
    if definition.position is ModificationPosition.PEPTIDE_C_TERM:
        allowed.add(ModificationPosition.PROTEIN_C_TERM)
    return allowed


def _site_compatibility_rejection(
    *,
    definition: StaticModification | VariableModification,
    site: ModificationPosition | None,
    residue: str | None,
    at_protein_n_term: bool,
    at_protein_c_term: bool,
    require_site_index: bool = False,
    site_index: int | None = None,
) -> ModificationRegistryRejection | None:
    if site is None:
        return None
    if site not in _allowed_sites(definition):
        return ModificationRegistryRejection(
            code="invalid_modification_site",
            message=(
                f"modification {definition.name!r} requires site {definition.position.value}, "
                f"got {site.value}"
            ),
        )
    if site is ModificationPosition.ANYWHERE and require_site_index and site_index is None:
        return ModificationRegistryRejection(
            code="missing_site_index",
            message=f"modification {definition.name!r} requires a residue site index",
        )
    if (
        site is ModificationPosition.ANYWHERE
        and residue is not None
        and definition.residues
        and residue not in definition.residues
    ):
        allowed = ",".join(definition.residues)
        suffix = (
            f" at position {site_index}" if site_index is not None else ""
        )
        return ModificationRegistryRejection(
            code="residue_incompatible",
            message=(
                f"modification {definition.name!r} is not valid on residue {residue}{suffix}; "
                f"expected one of {allowed}"
            ),
        )
    if site is ModificationPosition.PROTEIN_N_TERM and not at_protein_n_term:
        return ModificationRegistryRejection(
            code="protein_n_term_context_required",
            message=(
                f"modification {definition.name!r} requires a peptide at the protein N-terminus"
            ),
        )
    if site is ModificationPosition.PROTEIN_C_TERM and not at_protein_c_term:
        return ModificationRegistryRejection(
            code="protein_c_term_context_required",
            message=(
                f"modification {definition.name!r} requires a peptide at the protein C-terminus"
            ),
        )
    return None


def _residue_allowed(
    definition: StaticModification | VariableModification,
    residue: str | None,
) -> bool | None:
    if residue is None:
        return None
    if definition.position is not ModificationPosition.ANYWHERE:
        return True
    return residue in definition.residues


def _classify_resolution_source(
    definition: StaticModification | VariableModification,
    *,
    registry: ModificationRegistryDocument | None,
) -> ModificationRegistryResolutionSource:
    if registry is None:
        return ModificationRegistryResolutionSource.BUILTIN
    for candidate in (*registry.static_modifications, *registry.variable_modifications):
        if _same_definition(candidate, definition):
            return ModificationRegistryResolutionSource.REGISTRY
    builtin_registry = modification_registry()
    for candidate in (
        *builtin_registry.static_modifications,
        *builtin_registry.variable_modifications,
    ):
        if _same_definition(candidate, definition):
            return ModificationRegistryResolutionSource.BUILTIN
    return ModificationRegistryResolutionSource.REGISTRY


def _same_definition(
    left: _BaseModification,
    right: _BaseModification,
) -> bool:
    return (
        left.name == right.name
        and left.controlled_id == right.controlled_id
        and left.position == right.position
        and left.residues == right.residues
        and left.mass_delta_monoisotopic == right.mass_delta_monoisotopic
        and left.mass_delta_average == right.mass_delta_average
        and left.isotopic_label_family == right.isotopic_label_family
    )


def _registry_validation_signature(
    modification: _BaseModification,
) -> tuple[object, ...]:
    application = (
        "variable" if isinstance(modification, VariableModification) else "static"
    )
    return (
        application,
        modification.position,
        modification.residues,
        modification.mass_delta_monoisotopic,
        modification.mass_delta_average,
        tuple(
            (
                neutral_loss.name,
                neutral_loss.monoisotopic_mass,
                neutral_loss.average_mass,
            )
            for neutral_loss in modification.neutral_losses
        ),
        modification.isotopic_label_family,
        modification.max_occurrences
        if isinstance(modification, VariableModification)
        else None,
    )


def _raise_on_invalid_modification_registry(
    registry: ModificationRegistryDocument,
) -> None:
    report = validate_modification_registry(registry)
    if report.valid:
        return
    messages = "; ".join(issue.message for issue in report.issues)
    raise ValueError(f"invalid modification registry: {messages}")


def _registry_lookup(
    registry: ModificationRegistryDocument | None,
) -> dict[str, StaticModification | VariableModification]:
    mapping: dict[str, StaticModification | VariableModification] = {}
    for definition in _unique_registry_definitions(None):
        mapping[definition.name.strip().lower()] = definition
        if definition.controlled_id is not None:
            mapping[definition.controlled_id.strip().lower()] = definition
    if registry is None:
        return mapping
    for definition in _unique_registry_definitions(registry):
        mapping[definition.name.strip().lower()] = definition
        if definition.controlled_id is not None:
            mapping[definition.controlled_id.strip().lower()] = definition
    return mapping


def _unique_registry_definitions(
    registry: ModificationRegistryDocument | None,
) -> tuple[StaticModification | VariableModification, ...]:
    active = _BUILTIN_REGISTRY if registry is None else registry
    unique: list[StaticModification | VariableModification] = []
    active_definitions: tuple[StaticModification | VariableModification, ...] = (
        *active.static_modifications,
        *active.variable_modifications,
    )
    for definition in active_definitions:
        if any(_same_definition(existing, definition) for existing in unique):
            continue
        unique.append(definition)
    return tuple(unique)


def _definition_from_report(
    report: ModificationRegistryResolutionReport,
) -> StaticModification | VariableModification:
    if (
        not report.matched
        or report.modification_name is None
        or report.position is None
        or report.mass_delta_monoisotopic is None
        or report.mass_delta_average is None
        or report.application is None
    ):
        raise ValueError("modification resolution report does not contain a definition")
    if report.application == "static":
        return StaticModification(
            name=report.modification_name,
            residues=report.residues,
            position=report.position,
            mass_delta_monoisotopic=report.mass_delta_monoisotopic,
            mass_delta_average=report.mass_delta_average,
            elemental_composition_delta=report.elemental_composition_delta,
            neutral_losses=report.neutral_losses,
            controlled_id=report.controlled_id,
            isotopic_label_family=report.isotopic_label_family,
        )
    return VariableModification(
        name=report.modification_name,
        residues=report.residues,
        position=report.position,
        mass_delta_monoisotopic=report.mass_delta_monoisotopic,
        mass_delta_average=report.mass_delta_average,
        elemental_composition_delta=report.elemental_composition_delta,
        neutral_losses=report.neutral_losses,
        controlled_id=report.controlled_id,
        isotopic_label_family=report.isotopic_label_family,
    )


def _build_builtin_registry() -> ModificationRegistryDocument:
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="peptide_modification_registry",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    registry = ModificationRegistryDocument(
        document_schema=schema,
        static_modifications=(
            StaticModification(
                name="Carbamidomethyl",
                residues=("C",),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=57.021464,
                mass_delta_average=57.05132,
                elemental_composition_delta={"C": 2, "H": 3, "N": 1, "O": 1},
                controlled_id="UNIMOD:4",
            ),
        ),
        variable_modifications=(
            VariableModification(
                name="Oxidation",
                residues=("M",),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=15.994915,
                mass_delta_average=15.9994,
                elemental_composition_delta={"O": 1},
                controlled_id="UNIMOD:35",
            ),
            VariableModification(
                name="Phospho",
                residues=("S", "T", "Y"),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=79.966331,
                mass_delta_average=79.9799,
                elemental_composition_delta={"H": 1, "O": 3, "P": 1},
                neutral_losses=(
                    NeutralLoss(
                        name="phosphoric_acid",
                        monoisotopic_mass=_PHOSPHORIC_ACID_MONOISOTOPIC_MASS,
                        average_mass=_PHOSPHORIC_ACID_AVERAGE_MASS,
                    ),
                ),
                controlled_id="UNIMOD:21",
            ),
            VariableModification(
                name="Acetyl",
                position=ModificationPosition.PEPTIDE_N_TERM,
                mass_delta_monoisotopic=42.010565,
                mass_delta_average=42.0367,
                elemental_composition_delta={"C": 2, "H": 2, "O": 1},
                controlled_id="UNIMOD:1",
            ),
            VariableModification(
                name="AcetylLys",
                residues=("K",),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=42.010565,
                mass_delta_average=42.0367,
                elemental_composition_delta={"C": 2, "H": 2, "O": 1},
                controlled_id="BIJUX:ACETYL_LYS",
            ),
            VariableModification(
                name="Deamidated",
                residues=("N", "Q"),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=0.984016,
                mass_delta_average=0.9848,
                elemental_composition_delta={"H": -1, "N": -1, "O": 1},
                controlled_id="UNIMOD:7",
            ),
            VariableModification(
                name="Amidated",
                position=ModificationPosition.PEPTIDE_C_TERM,
                mass_delta_monoisotopic=-0.984016,
                mass_delta_average=-0.9848,
                elemental_composition_delta={"H": 1, "N": 1, "O": -1},
                controlled_id="UNIMOD:2",
            ),
            VariableModification(
                name="HeavyLys8",
                residues=("K",),
                position=ModificationPosition.ANYWHERE,
                mass_delta_monoisotopic=8.014199,
                mass_delta_average=8.014199,
                controlled_id="BIJUX:HEAVY_LYS8",
                isotopic_label_family="silac_lys",
            ),
        ),
    )
    _raise_on_invalid_modification_registry(registry)
    payload = registry.to_dict()
    return registry.model_copy(
        update={"document_schema": registry.document_schema.with_content_hash(payload)}
    )


_BUILTIN_REGISTRY = _build_builtin_registry()
_MODIFICATION_TOKEN_ALIASES = {
    "acetylation": "acetyl",
    "acetylk": "acetyllys",
    "acetyllys": "acetyllys",
    "acetyllysine": "acetyllys",
    "carbamidomethylation": "carbamidomethyl",
    "deamidation": "deamidated",
    "deamidated": "deamidated",
    "heavylys8": "heavylys8",
    "lysine acetylation": "acetyllys",
    "oxidation": "oxidation",
    "phosphorylation": "phospho",
}
_MODIFICATION_TOKEN_FAMILIES = {
    "acetyl": ("acetyl", "acetyllys"),
    "acetylation": ("acetyl", "acetyllys"),
    "acetylk": ("acetyllys",),
    "acetyllys": ("acetyllys",),
    "acetyllysine": ("acetyllys",),
    "lysine acetylation": ("acetyllys",),
}


__all__ = [
    "ModificationRegistryRejection",
    "ModificationRegistryResolutionMode",
    "ModificationRegistryResolutionReport",
    "ModificationRegistryResolutionSource",
    "build_modification_registry",
    "get_modification",
    "load_modification_registry",
    "modification_registry",
    "resolve_modification",
    "resolve_modification_definition",
    "resolve_modification_site",
    "validate_modification_registry",
]
