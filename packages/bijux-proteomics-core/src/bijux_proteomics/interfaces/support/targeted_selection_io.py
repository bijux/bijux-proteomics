# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Targeted-selection input loaders shared by CLI command modules."""

from __future__ import annotations

from typing import TypedDict, cast

from .imports import *  # noqa: F401,F403


class _SelectedTransitionAssayPayload(TypedDict):
    target_protein_ref: str
    target_protein_group_id: str
    gene_symbol: str | None
    peptide_sequence: str
    canonical_peptide: str
    peptide_rank: int
    precursor_charge: int
    precursor_mz: float
    source_library_entry_id: str | None
    chemistry_supported_transition_count: int
    selected_transition_count: int
    sufficient_transition_support: bool
    instrument_caveats: tuple[str, ...]
    selected_transitions: list[TargetedTransitionSelectionFragment]


def _load_similarity_spectra(
    input_path: Path, *, kind: str
) -> tuple[SpectrumModel, ...]:
    resolved_kind = kind
    if resolved_kind == "auto":
        suffix = input_path.suffix.lower()
        if suffix == ".mgf":
            resolved_kind = "mgf"
        elif suffix == ".mzml":
            resolved_kind = "mzml"
        else:
            raise ValueError(
                f"cannot infer spectrum input kind for {input_path.name!r}; "
                "use --query-kind/--reference-kind mgf or mzml"
            )
    if resolved_kind == "mgf":
        return cast(tuple[SpectrumModel, ...], parse_mgf(input_path).accepted_spectra)
    if resolved_kind == "mzml":
        return cast(tuple[SpectrumModel, ...], parse_mzml(input_path).accepted_spectra)
    raise ValueError("spectrum similarity supports only mgf and mzml inputs")


def _select_similarity_spectrum(
    spectra: tuple[SpectrumModel, ...],
    *,
    input_path: Path,
    spectrum_id: str | None,
) -> SpectrumModel:
    if not spectra:
        raise ValueError(
            f"{input_path.name!r} does not contain an accepted spectrum for comparison"
        )
    if spectrum_id is None:
        return spectra[0]
    try:
        return next(item for item in spectra if item.spectrum_id == spectrum_id)
    except StopIteration as exc:
        raise ValueError(
            f"unknown spectrum id {spectrum_id!r} in {input_path.name!r}"
        ) from exc


def _load_protein_group_map(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("protein group map must include a header row")
        required = {"accession", "protein_group"}
        missing = required.difference(reader.fieldnames)
        if missing:
            missing_columns = ", ".join(sorted(missing))
            raise ValueError(
                "protein group map must include the columns "
                f"'accession' and 'protein_group'; missing: {missing_columns}"
            )
        mapping: dict[str, str] = {}
        for row in reader:
            accession = str(row.get("accession", "")).strip()
            protein_group = str(row.get("protein_group", "")).strip()
            if not accession or not protein_group:
                raise ValueError(
                    "protein group map rows must provide both accession and protein_group"
                )
            mapping[accession] = protein_group
    return mapping


def _parse_cli_bool(raw_value: object, *, field_name: str) -> bool:
    value = str(raw_value).strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    raise ValueError(f"field {field_name!r} must be a boolean string")


def _split_semicolon_field(raw_value: object) -> tuple[str, ...]:
    return tuple(
        token
        for raw_token in str(raw_value or "").split(";")
        if (token := raw_token.strip())
    )


def _load_targeted_selection_targets(
    path: Path,
) -> tuple[DiscoveryTargetProteinEntry, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "protein-card TSV must include a header row for targeted peptide selection"
            )
        required_columns = {"protein_group_id", "representative_protein_ref"}
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "protein-card TSV is missing required columns for targeted peptide selection: "
                + ", ".join(sorted(missing_columns))
            )
        targets: list[DiscoveryTargetProteinEntry] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                representative_protein_ref = str(
                    row.get("representative_protein_ref", "")
                ).strip()
                protein_group_id = str(row.get("protein_group_id", "")).strip()
                if not representative_protein_ref or not protein_group_id:
                    raise ValueError(
                        "protein_group_id and representative_protein_ref are required"
                    )
                targets.append(
                    DiscoveryTargetProteinEntry(
                        protein_group_id=protein_group_id,
                        representative_protein_ref=representative_protein_ref,
                        protein_refs=_split_semicolon_field(
                            row.get("protein_refs", "")
                        ),
                        gene_symbol=(
                            gene_symbol
                            if (gene_symbol := str(row.get("gene_symbol", "")).strip())
                            else None
                        ),
                        discovery_peptides=_split_semicolon_field(
                            row.get("peptides", "")
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid protein-card row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(targets)


def _load_peptide_evidence_entries(path: Path) -> tuple[PeptideEvidenceEntry, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "peptide-evidence TSV must include a header row for targeted peptide selection"
            )
        required_columns = {
            "peptide",
            "canonical_peptide",
            "primary_class",
            "peptide_q_value",
            "accepted",
            "psm_count",
            "spectrum_count",
            "run_count",
            "detection_frequency",
            "replicate_consistency",
            "condition_specificity",
            "detected_condition_count",
            "reproducibility_class",
            "best_score",
            "charge_states",
            "run_ids",
            "protein_refs",
            "target_decoy_label",
            "target_decoy_contaminant_class",
            "contaminant_flag",
            "explanation",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "peptide-evidence TSV is missing required columns for targeted peptide selection: "
                + ", ".join(sorted(missing_columns))
            )
        entries: list[PeptideEvidenceEntry] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                entries.append(
                    PeptideEvidenceEntry(
                        peptide=str(row.get("peptide", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        primary_class=PeptideEvidenceClass(
                            str(row.get("primary_class", "")).strip()
                        ),
                        tags=(),
                        peptide_q_value=float(
                            str(row.get("peptide_q_value", "")).strip()
                        ),
                        accepted=_parse_cli_bool(
                            row.get("accepted", ""), field_name="accepted"
                        ),
                        psm_count=int(str(row.get("psm_count", "")).strip()),
                        spectrum_count=int(str(row.get("spectrum_count", "")).strip()),
                        run_count=int(str(row.get("run_count", "")).strip()),
                        detection_frequency=float(
                            str(row.get("detection_frequency", "")).strip()
                        ),
                        replicate_consistency=float(
                            str(row.get("replicate_consistency", "")).strip()
                        ),
                        condition_specificity=float(
                            str(row.get("condition_specificity", "")).strip()
                        ),
                        detected_condition_count=int(
                            str(row.get("detected_condition_count", "")).strip()
                        ),
                        reproducibility_class=CrossRunReproducibilityClass(
                            str(row.get("reproducibility_class", "")).strip()
                        ),
                        exploratory_override=_parse_cli_bool(
                            row.get("exploratory_override", "false"),
                            field_name="exploratory_override",
                        ),
                        best_score=float(str(row.get("best_score", "")).strip()),
                        charge_states=tuple(
                            int(token)
                            for token in _split_semicolon_field(
                                row.get("charge_states", "")
                            )
                        ),
                        run_ids=_split_semicolon_field(row.get("run_ids", "")),
                        protein_refs=_split_semicolon_field(
                            row.get("protein_refs", "")
                        ),
                        target_decoy_label=TargetDecoyLabel(
                            str(row.get("target_decoy_label", "")).strip()
                        ),
                        target_decoy_contaminant_class=TargetDecoyContaminantClass(
                            str(row.get("target_decoy_contaminant_class", "")).strip()
                        ),
                        contaminant_flag=_parse_cli_bool(
                            row.get("contaminant_flag", "false"),
                            field_name="contaminant_flag",
                        ),
                        explanation=str(row.get("explanation", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid peptide-evidence row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(entries)


def _load_selected_targeted_peptides(
    path: Path,
) -> tuple[DiscoveryTargetedPeptideSelectionEntry, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "selected-peptide TSV must include a header row for targeted transition selection"
            )
        required_columns = {
            "target_protein_ref",
            "target_protein_group_id",
            "rank",
            "candidate_source",
            "peptide_sequence",
            "canonical_peptide",
            "observed_in_discovery",
            "uniqueness_class",
            "uniqueness_score",
            "detectability_score",
            "detectability_tier",
            "suitability_score",
            "liability_tier",
            "selection_score",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "selected-peptide TSV is missing required columns for targeted transition selection: "
                + ", ".join(sorted(missing_columns))
            )
        entries: list[DiscoveryTargetedPeptideSelectionEntry] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                primary_evidence_class_raw = str(
                    row.get("primary_evidence_class", "")
                ).strip()
                entries.append(
                    DiscoveryTargetedPeptideSelectionEntry(
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            value
                            if (value := str(row.get("gene_symbol", "")).strip())
                            else None
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        candidate_source=TargetedPeptideCandidateSource(
                            str(row.get("candidate_source", "")).strip()
                        ),
                        rank=int(str(row.get("rank", "")).strip()),
                        observed_in_discovery=_parse_cli_bool(
                            row.get("observed_in_discovery", ""),
                            field_name="observed_in_discovery",
                        ),
                        observed_psm_count=(
                            None
                            if not str(row.get("observed_psm_count", "")).strip()
                            else int(str(row.get("observed_psm_count", "")).strip())
                        ),
                        run_count=(
                            None
                            if not str(row.get("run_count", "")).strip()
                            else int(str(row.get("run_count", "")).strip())
                        ),
                        detection_frequency=(
                            None
                            if not str(row.get("detection_frequency", "")).strip()
                            else float(str(row.get("detection_frequency", "")).strip())
                        ),
                        replicate_consistency=(
                            None
                            if not str(row.get("replicate_consistency", "")).strip()
                            else float(
                                str(row.get("replicate_consistency", "")).strip()
                            )
                        ),
                        primary_evidence_class=(
                            None
                            if not primary_evidence_class_raw
                            else PeptideEvidenceClass(primary_evidence_class_raw)
                        ),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        uniqueness_score=float(
                            str(row.get("uniqueness_score", "")).strip()
                        ),
                        detectability_score=float(
                            str(row.get("detectability_score", "")).strip()
                        ),
                        detectability_tier=PeptideDetectabilityTier(
                            str(row.get("detectability_tier", "")).strip()
                        ),
                        suitability_score=float(
                            str(row.get("suitability_score", "")).strip()
                        ),
                        liability_tier=PeptideChemicalLiabilityTier(
                            str(row.get("liability_tier", "")).strip()
                        ),
                        liability_codes=_split_semicolon_field(
                            row.get("liability_codes", "")
                        ),
                        selection_score=float(
                            str(row.get("selection_score", "")).strip()
                        ),
                        selection_reasons=_split_semicolon_field(
                            row.get("selection_reasons", "")
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid selected-peptide row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(entries)


def _load_selected_targeted_transitions(
    path: Path,
) -> tuple[TargetedTransitionSelectionPeptideEntry, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "selected-transition TSV must include a header row for targeted assay interference review"
            )
        required_columns = {
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "peptide_sequence",
            "canonical_peptide",
            "peptide_rank",
            "precursor_charge",
            "precursor_mz",
            "source_library_entry_id",
            "chemistry_supported_transition_count",
            "selected_transition_count",
            "sufficient_transition_support",
            "transition_rank",
            "fragment_label",
            "ion_type",
            "fragment_ordinal",
            "fragment_charge",
            "fragment_sequence",
            "fragment_mz",
            "expected_relative_intensity",
            "interference_risk",
            "interference_risk_score",
            "interference_risk_reasons",
            "selection_score",
            "selection_reasons",
            "instrument_caveats",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "selected-transition TSV is missing required columns for targeted assay interference review: "
                + ", ".join(sorted(missing_columns))
            )
        entries_by_assay: dict[str, _SelectedTransitionAssayPayload] = {}
        assay_order: list[str] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                assay_entry_id = str(row.get("assay_entry_id", "")).strip()
                if assay_entry_id not in entries_by_assay:
                    assay_order.append(assay_entry_id)
                    entries_by_assay[assay_entry_id] = {
                        "target_protein_ref": str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        "target_protein_group_id": str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        "gene_symbol": (
                            value
                            if (value := str(row.get("gene_symbol", "")).strip())
                            else None
                        ),
                        "peptide_sequence": str(
                            row.get("peptide_sequence", "")
                        ).strip(),
                        "canonical_peptide": str(
                            row.get("canonical_peptide", "")
                        ).strip(),
                        "peptide_rank": int(str(row.get("peptide_rank", "")).strip()),
                        "precursor_charge": int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        "precursor_mz": float(str(row.get("precursor_mz", "")).strip()),
                        "source_library_entry_id": (
                            value
                            if (
                                value := str(
                                    row.get("source_library_entry_id", "")
                                ).strip()
                            )
                            else None
                        ),
                        "chemistry_supported_transition_count": int(
                            str(
                                row.get("chemistry_supported_transition_count", "")
                            ).strip()
                        ),
                        "selected_transition_count": int(
                            str(row.get("selected_transition_count", "")).strip()
                        ),
                        "sufficient_transition_support": _parse_cli_bool(
                            row.get("sufficient_transition_support", ""),
                            field_name="sufficient_transition_support",
                        ),
                        "instrument_caveats": _split_semicolon_field(
                            row.get("instrument_caveats", "")
                        ),
                        "selected_transitions": [],
                    }
                selected_transitions = entries_by_assay[assay_entry_id][
                    "selected_transitions"
                ]
                selected_transitions.append(
                    TargetedTransitionSelectionFragment(
                        rank=int(str(row.get("transition_rank", "")).strip()),
                        fragment_label=str(row.get("fragment_label", "")).strip(),
                        ion_type=FragmentIonSeries(
                            str(row.get("ion_type", "")).strip()
                        ),
                        fragment_ordinal=int(
                            str(row.get("fragment_ordinal", "")).strip()
                        ),
                        fragment_charge=int(
                            str(row.get("fragment_charge", "")).strip()
                        ),
                        fragment_sequence=str(row.get("fragment_sequence", "")).strip(),
                        fragment_mz=float(str(row.get("fragment_mz", "")).strip()),
                        expected_relative_intensity=(
                            None
                            if not str(
                                row.get("expected_relative_intensity", "")
                            ).strip()
                            else float(
                                str(row.get("expected_relative_intensity", "")).strip()
                            )
                        ),
                        interference_risk=TargetedTransitionInterferenceRisk(
                            str(row.get("interference_risk", "")).strip()
                        ),
                        interference_risk_score=float(
                            str(row.get("interference_risk_score", "")).strip()
                        ),
                        interference_risk_reasons=_split_semicolon_field(
                            row.get("interference_risk_reasons", "")
                        ),
                        selection_score=float(
                            str(row.get("selection_score", "")).strip()
                        ),
                        selection_reasons=_split_semicolon_field(
                            row.get("selection_reasons", "")
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid selected-transition row {row_number} in {path.name!r}: {exc}"
                ) from exc
    entries: list[TargetedTransitionSelectionPeptideEntry] = []
    for assay_entry_id in assay_order:
        assay_payload = entries_by_assay[assay_entry_id]
        ordered_transitions = tuple(
            sorted(
                assay_payload["selected_transitions"],
                key=lambda fragment: (fragment.rank, fragment.fragment_mz),
            )
        )
        entries.append(
            TargetedTransitionSelectionPeptideEntry(
                assay_entry_id=assay_entry_id,
                target_protein_ref=assay_payload["target_protein_ref"],
                target_protein_group_id=assay_payload["target_protein_group_id"],
                gene_symbol=assay_payload["gene_symbol"],
                peptide_sequence=assay_payload["peptide_sequence"],
                canonical_peptide=assay_payload["canonical_peptide"],
                peptide_rank=assay_payload["peptide_rank"],
                precursor_charge=assay_payload["precursor_charge"],
                precursor_mz=assay_payload["precursor_mz"],
                source_library_entry_id=assay_payload["source_library_entry_id"],
                chemistry_supported_transition_count=assay_payload[
                    "chemistry_supported_transition_count"
                ],
                selected_transition_count=assay_payload["selected_transition_count"],
                sufficient_transition_support=assay_payload[
                    "sufficient_transition_support"
                ],
                instrument_caveats=assay_payload["instrument_caveats"],
                selected_transitions=ordered_transitions,
            )
        )
    return tuple(entries)


def _read_summary_field_map(
    path: Path,
    *,
    description: str,
) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(f"{description} must include a header row")
        required_columns = {"field", "value"}
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                f"{description} is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )
        return {
            str(row.get("field", "")).strip(): str(row.get("value", "")).strip()
            for row in reader
        }


def _require_report_artifact(
    report_dir: Path,
    artifact_name: str,
    *,
    description: str,
) -> Path:
    artifact_path = report_dir / artifact_name
    if not artifact_path.exists():
        raise click.ClickException(
            f"{description} is missing required artifact {artifact_name!r}"
        )
    return artifact_path


def _load_selected_peptide_support_by_protein(
    path: Path,
) -> dict[str, dict[str, float]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "selected-peptide TSV must include a header row for biomarker candidate ranking"
            )
        required_columns = {
            "target_protein_ref",
            "detectability_score",
            "uniqueness_score",
            "suitability_score",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "selected-peptide TSV is missing required columns for biomarker candidate ranking: "
                + ", ".join(sorted(missing_columns))
            )
        support_by_protein: dict[str, dict[str, float]] = {}
        for row_number, row in enumerate(reader, start=2):
            try:
                protein_ref = str(row.get("target_protein_ref", "")).strip()
                support = support_by_protein.setdefault(
                    protein_ref,
                    {
                        "detectability_score": 0.0,
                        "uniqueness_score": 0.0,
                        "suitability_score": 0.0,
                    },
                )
                support["detectability_score"] = max(
                    support["detectability_score"],
                    float(str(row.get("detectability_score", "")).strip()),
                )
                support["uniqueness_score"] = max(
                    support["uniqueness_score"],
                    float(str(row.get("uniqueness_score", "")).strip()),
                )
                support["suitability_score"] = max(
                    support["suitability_score"],
                    float(str(row.get("suitability_score", "")).strip()),
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid selected-peptide row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return support_by_protein


def _load_assay_interference_support_by_protein(
    path: Path,
) -> dict[str, dict[str, float | bool]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "assay-interference TSV must include a header row for biomarker candidate ranking"
            )
        required_columns = {
            "target_protein_ref",
            "interference_risk_score",
            "panel_export_allowed",
            "exported_transition_count",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "assay-interference TSV is missing required columns for biomarker candidate ranking: "
                + ", ".join(sorted(missing_columns))
            )
        support_by_protein: dict[str, dict[str, float | bool]] = {}
        for row_number, row in enumerate(reader, start=2):
            try:
                protein_ref = str(row.get("target_protein_ref", "")).strip()
                panel_export_allowed = _parse_cli_bool(
                    row.get("panel_export_allowed", ""),
                    field_name="panel_export_allowed",
                )
                risk_score = float(str(row.get("interference_risk_score", "")).strip())
                exported_transition_count = int(
                    str(row.get("exported_transition_count", "")).strip()
                )
                assay_score = max(
                    0.0,
                    (
                        (1.0 - risk_score)
                        * (1.0 if panel_export_allowed else 0.35)
                        * min(1.0, exported_transition_count / 3.0)
                    ),
                )
                current = support_by_protein.get(protein_ref)
                if current is None or assay_score > float(current["assay_score"]):
                    support_by_protein[protein_ref] = {
                        "assay_score": assay_score,
                        "panel_export_allowed": panel_export_allowed,
                        "risk_score": risk_score,
                    }
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid assay-interference row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return support_by_protein


__all__ = [
    "Any",
    "BiologicalContextColumnMapping",
    "BiologicalContextKind",
    "BiomarkerCandidateKind",
    "BiomarkerCandidateRankingInput",
    "BiomarkerStabilityPolicy",
    "BiomarkerStabilityReasonCode",
    "CompartmentBiologyPolicy",
    "ComplexActivityPolicy",
    "ComplexEnrichmentCorrectionPolicy",
    "ComplexMembershipColumnMapping",
    "CrossRunReproducibilityClass",
    "DecoyGenerationMode",
    "DiaPeptideRollupMethod",
    "DiaPrecursorMatrixPolicy",
    "DiaPrecursorQValueFilterTiming",
    "DiaProteinMatrixTargetKind",
    "DiaProteinRollupMethod",
    "DiaSharedPeptidePolicy",
    "DifferentialAbundanceTestType",
    "DiscoveryTargetProteinEntry",
    "DiscoveryTargetedPeptideSelectionEntry",
    "DiseasePhenotypeInterpretationPolicy",
    "DrugTargetInterpretationPolicy",
    "DuplicateAccessionPolicy",
    "ExperimentalDesignEntry",
    "FailureExplanationRequest",
    "FastaDatabaseProfile",
    "FastaParseMode",
    "FastaParseReport",
    "FdrPolicy",
    "FormatConversionTarget",
    "FragmentIonSeries",
    "GoAnnotationColumnMapping",
    "GoEnrichmentCorrectionPolicy",
    "HeatmapMissingValuePolicy",
    "HeatmapPreparationPolicy",
    "ImputationMethod",
    "IsotopicLabelingPolicy",
    "ModificationRegistryDocument",
    "Ms1FeatureColumnMapping",
    "NormalizationMethod",
    "NormalizedProteinRecord",
    "OrthologColumnMapping",
    "PairedDifferentialPolicy",
    "PanelRedundancyCandidateInput",
    "PanelRedundancyPolicy",
    "ParsimonyVariant",
    "Path",
    "PathwayActivityPolicy",
    "PathwayEnrichmentCorrectionPolicy",
    "PathwayMembershipColumnMapping",
    "PeptideChemicalLiabilityTier",
    "PeptideDetectabilityTier",
    "PeptideDigestionMode",
    "PeptideEvidenceClass",
    "PeptideEvidenceEntry",
    "PeptideMatrixGroupingMode",
    "PeptideUniquenessClass",
    "PowerEstimationPolicy",
    "PpiEdgeColumnMapping",
    "PrecursorIntensityColumnMapping",
    "PrecursorMassErrorQuery",
    "ProgramSpec",
    "ProteaseRule",
    "ProteinAnnotationColumnMapping",
    "ProteinMatrixTargetKind",
    "ProteinReferenceColumnMapping",
    "ProteinReferenceEntry",
    "ProteinSetColumnMapping",
    "ProteinSetEnrichmentMissingBackgroundPolicy",
    "ProteinSetEnrichmentPolicy",
    "ProteinSetScoringPolicy",
    "ProteomicsFormatKind",
    "ProteomicsOperatorError",
    "ProteomicsOperatorErrorCode",
    "PsmRecord",
    "PtmLocalizationColumnMapping",
    "PtmMotifBackgroundMode",
    "PtmMotifComparisonPolicy",
    "PtmMotifRegulationDirection",
    "PtmPeptideColumnMapping",
    "PtmPhosphositeSelectionPolicy",
    "PtmProteinCorrectionMode",
    "PtmRegulatorEnrichmentPolicy",
    "PtmSiteAnnotationColumnMapping",
    "PtmSiteContextColumnMapping",
    "PtmSiteQuantAmbiguityPolicy",
    "QcEvidenceInputFile",
    "QuantEntityLevel",
    "QuantMeasureKind",
    "QuantRollupMethod",
    "RegulatorEvidenceColumnMapping",
    "RegulatorSiteSignalColumnMapping",
    "ResultExplanationKind",
    "ResultExplanationRequest",
    "ResultQueryKind",
    "ResultQueryRequest",
    "RunDetectionContext",
    "ScoreOrientation",
    "SearchAdapterKind",
    "SearchEngineModifiedPeptideDialect",
    "SearchResultColumnMapping",
    "SilacColumnMapping",
    "SilacLabel",
    "SilacQuantificationPolicy",
    "SilacValidationPolicy",
    "SpectralLibraryEntry",
    "SpectralLibraryFormat",
    "SpectralSimilarityMethod",
    "SpectrumModel",
    "SpectrumSimilarityMode",
    "StaticModification",
    "TargetDecoyContaminantClass",
    "TargetDecoyLabel",
    "TargetDecoyLabelPolicy",
    "TargetDecoyReferenceCase",
    "TargetPanelSourceKind",
    "TargetedAssayInterferenceReason",
    "TargetedAssayInterferenceRiskTier",
    "TargetedPanelAssayInput",
    "TargetedPanelBiomarkerCandidateInput",
    "TargetedPanelCandidateKind",
    "TargetedPanelSelectedPeptideInput",
    "TargetedPanelTransitionInput",
    "TargetedPanelWarningCode",
    "TargetedPeptideCandidateSource",
    "TargetedResultSourceKind",
    "TargetedResultValidationPolicy",
    "TargetedTransitionInterferenceRisk",
    "TargetedTransitionSelectionFragment",
    "TargetedTransitionSelectionPeptideEntry",
    "TargetedValidationDiscoveryClaimInput",
    "TargetedValidationPanelAssayInput",
    "TargetedValidationReasonCode",
    "TargetedValidationVerdict",
    "TimeCourseTestingPolicy",
    "TmtInterferencePolicy",
    "TmtNormalizationMethod",
    "TmtNormalizationPolicy",
    "TmtPlexIntegrationPolicy",
    "TmtReporterChannelColumn",
    "TmtReporterColumnMapping",
    "TmtSearchResultSourceKind",
    "TmtValidationPolicy",
    "ValidationEvidenceDiscoveryInput",
    "ValidationEvidenceOmittedCandidateInput",
    "ValidationEvidencePanelAssayInput",
    "ValidationEvidenceRedundancyInput",
    "ValidationEvidenceResultAssayInput",
    "ValidationEvidenceResultInput",
    "ValidationEvidenceStabilityInput",
    "ValidationExperimentPlanningPolicy",
    "ValidationPlanningBiomarkerCandidateInput",
    "ValidationPlanningOmittedCandidateInput",
    "ValidationPlanningPanelAssayInput",
    "ValidationPlanningPilotVarianceInput",
    "ValidationPlanningSelectedPeptideInput",
    "VariableModification",
    "VolcanoReviewPolicy",
    "WorkflowSchedulerKind",
    "_load_assay_interference_support_by_protein",
    "_load_peptide_evidence_entries",
    "_load_protein_group_map",
    "_load_selected_peptide_support_by_protein",
    "_load_selected_targeted_peptides",
    "_load_selected_targeted_transitions",
    "_load_similarity_spectra",
    "_load_targeted_selection_targets",
    "_parse_cli_bool",
    "_read_summary_field_map",
    "_require_report_artifact",
    "_select_similarity_spectrum",
    "_split_semicolon_field",
    "annotate_psm_error_rates",
    "annotate_spectrum_fragments",
    "append_contaminant_database",
    "apply_benjamini_hochberg",
    "apply_complex_enrichment_multiple_testing",
    "apply_go_enrichment_multiple_testing",
    "apply_pathway_enrichment_multiple_testing",
    "apply_q_values",
    "approximate_peptide_isotope_envelope",
    "assign_confidence_labels",
    "assign_razor_peptides",
    "build_analysis_recommendation_report_from_artifacts",
    "build_batch_effect_estimator_report",
    "build_batch_qc_assessment",
    "build_belief_audit_report_from_artifacts",
    "build_biological_context_mapping_report",
    "build_biomarker_candidate_ranking_report",
    "build_biomarker_stability_report",
    "build_calibration_plot_data",
    "build_comet_import_report",
    "build_compact_result_summary_report_from_artifacts",
    "build_compartment_biology_report",
    "build_complex_activity_report",
    "build_complex_enrichment_report",
    "build_contaminant_evidence_report",
    "build_contaminant_peptide_match_report",
    "build_core_protein_inference_benchmark_suite",
    "build_decoy_generation_manifest",
    "build_decoy_generation_report",
    "build_dia_protein_matrix_report",
    "build_dia_volcano_review",
    "build_diann_import_report",
    "build_diann_library_coverage_report",
    "build_diann_peptide_matrix_report",
    "build_diann_peptide_target_panel_report",
    "build_diann_precursor_matrix_report",
    "build_diann_protein_target_panel_report",
    "build_diann_run_qc_report",
    "build_differential_abundance_report",
    "build_digest_manifest",
    "build_discovery_targeted_peptide_selection_report",
    "build_disease_phenotype_interpretation_report",
    "build_drug_target_interpretation_report",
    "build_evidence_level_fdr_review_report",
    "build_experiment_feasibility_report",
    "build_failure_explanation_report",
    "build_fasta_database_profile",
    "build_fasta_provenance_manifest",
    "build_fasta_stats",
    "build_fdr_audit_trail",
    "build_fragment_ion_review_report",
    "build_fragpipe_import_benchmark_report",
    "build_fragpipe_import_report",
    "build_generic_psm_mapper_report",
    "build_go_enrichment_report",
    "build_heatmap_preparation_report",
    "build_imputation_report",
    "build_imputation_sensitivity_report",
    "build_instrument_batch_qc_report",
    "build_lab_protocol_interpretation_profile",
    "build_label_based_volcano_review",
    "build_label_free_intensity_table",
    "build_lcms_run_qc_report",
    "build_lfq_peptide_target_panel_report",
    "build_lfq_protein_lfq_target_panel_report",
    "build_lfq_protein_target_panel_report",
    "build_limma_compatible_quant_package",
    "build_maxquant_import_report",
    "build_missingness_classifier_report",
    "build_modification_localization_advisory",
    "build_modification_resolution_report",
    "build_modified_peptide",
    "build_msstats_compatible_input_report",
    "build_multi_condition_differential_abundance_report",
    "build_multi_contrast_consistency_report",
    "build_multiplex_metadata_validation_report",
    "build_mzml_collection_summary",
    "build_mzml_practical_review_report",
    "build_normalization_comparison_report",
    "build_normalization_strategy_comparison_report",
    "build_normalized_run_bundle",
    "build_openms_import_report",
    "build_ortholog_mapping_report",
    "build_panel_redundancy_report",
    "build_parsimony_review_report",
    "build_pathway_activity_report",
    "build_pathway_enrichment_report",
    "build_peptide_charge_state",
    "build_peptide_cross_run_reproducibility_report",
    "build_peptide_database_lookup_report",
    "build_peptide_detectability_report",
    "build_peptide_elemental_composition",
    "build_peptide_evidence_review_report",
    "build_peptide_intensity_matrix_from_features",
    "build_peptide_intensity_matrix_from_precursors",
    "build_peptide_intensity_matrix_from_psms",
    "build_peptide_profile_inconsistency_report",
    "build_peptide_property_report",
    "build_peptide_summary_report",
    "build_peptide_uniqueness_across_database",
    "build_performance_snapshot",
    "build_picked_protein_fdr_review_report",
    "build_power_estimation_report",
    "build_ppi_network_module_report",
    "build_precursor_mass_error_report",
    "build_protein_ambiguity_review_report",
    "build_protein_annotation_mapping_report",
    "build_protein_coverage_map",
    "build_protein_coverage_plot_report",
    "build_protein_coverage_review_report",
    "build_protein_cross_run_reproducibility_report",
    "build_protein_evidence_review_report",
    "build_protein_grouping_review_report",
    "build_protein_groups",
    "build_protein_intensity_matrix_from_features",
    "build_protein_intensity_matrix_from_psms",
    "build_protein_lfq_report_from_peptides",
    "build_protein_set_enrichment_report",
    "build_protein_set_scoring_report",
    "build_protein_summary_report",
    "build_proteomics_workflow_runtime_bundle",
    "build_protocol_aware_qc_threshold_policy",
    "build_protocol_consistency_report",
    "build_psm_error_rate_annotation_report",
    "build_psm_evidence_inspection_report",
    "build_psm_summary_report",
    "build_psm_target_decoy_fdr_report",
    "build_ptm_ambiguity_review_report",
    "build_ptm_differential_analysis_report",
    "build_ptm_differential_volcano_plot",
    "build_ptm_enrichment_input",
    "build_ptm_localization_scoring_report",
    "build_ptm_motif_windows",
    "build_ptm_occupancy_counterpart_report",
    "build_ptm_phosphosite_motif_enrichment_report",
    "build_ptm_protein_site_mapping_report",
    "build_ptm_regulator_enrichment_report",
    "build_ptm_site_annotation_biology_summary",
    "build_ptm_site_annotation_mapping_report",
    "build_ptm_site_context_report",
    "build_ptm_site_coverage_report",
    "build_ptm_site_fdr",
    "build_ptm_site_group_quantification_report",
    "build_ptm_site_occupancy_report",
    "build_ptm_site_quantification_report",
    "build_ptm_site_table",
    "build_ptm_volcano_review",
    "build_qc_evidence_manifest",
    "build_quant_design_matrix_report",
    "build_regulator_inference_report",
    "build_replicate_and_batch_qc_report",
    "build_result_explanation_report_from_artifacts",
    "build_result_query_report_from_artifacts",
    "build_run_qc_assessment",
    "build_sage_import_report",
    "build_sample_exploration_report",
    "build_sample_sheet_repair_suggestion_report",
    "build_score_separation_diagnostic_report",
    "build_search_adapter_capability_matrix",
    "build_search_adapter_conformance_report",
    "build_search_adapter_provenance_manifest",
    "build_search_engine_modified_peptide_report",
    "build_search_result_provenance_manifest",
    "build_silac_ratio_report",
    "build_silac_validation_report",
    "build_skyline_result_import_report",
    "build_spectral_count_table",
    "build_spectral_library_index",
    "build_spectral_library_summary",
    "build_spectronaut_import_report",
    "build_spectronaut_peptide_matrix_report",
    "build_spectronaut_precursor_matrix_report",
    "build_spectronaut_protein_matrix_report",
    "build_spectrum_collection_summary",
    "build_spectrum_library_similarity_report",
    "build_spectrum_metrics",
    "build_spectrum_peak_match_report",
    "build_spectrum_plot_payload",
    "build_spectrum_provenance_manifest",
    "build_spectrum_run_qc_plot_payload",
    "build_spectrum_run_qc_report",
    "build_spectrum_similarity_comparison_report",
    "build_spectrum_summary_table_report",
    "build_statistical_backend_validation_report",
    "build_streaming_parse_profile",
    "build_target_decoy_reference_validation_report",
    "build_targeted_assay_interference_report",
    "build_targeted_carryover_report",
    "build_targeted_panel_design_report",
    "build_targeted_result_validation_report",
    "build_targeted_transition_selection_report",
    "build_theoretical_digest_bundle",
    "build_time_course_differential_report",
    "build_tmt_interference_report",
    "build_tmt_normalization_report",
    "build_tmt_plex_integration_report",
    "build_tmt_ratio_report",
    "build_tmt_reporter_feature_bundle",
    "build_tmt_reporter_matrix_report",
    "build_tmt_validation_report",
    "build_transition_qc_report_from_table",
    "build_transition_table_result_import_report",
    "build_validation_evidence_card_report",
    "build_validation_experiment_planning_report",
    "build_workflow_runtime_validation_report",
    "calculate_fragment_ions",
    "calculate_grouped_fdr",
    "calculate_level_specific_fdr",
    "calculate_picked_protein_fdr",
    "canonicalize_modified_peptide",
    "click",
    "compare_search_result_reports",
    "convert_proteomics_format",
    "create_program_spec",
    "csv",
    "deduplicate_fasta_records",
    "default_qc_threshold_policy",
    "digest_protein_records",
    "export_batch_effect_batches_tsv",
    "export_batch_effect_principal_components_tsv",
    "export_batch_effect_summary_tsv",
    "export_differential_abundance_tsv",
    "export_differential_broken_pairs_tsv",
    "export_heatmap_column_metadata_tsv",
    "export_heatmap_matrix_tsv",
    "export_heatmap_row_metadata_tsv",
    "export_heatmap_summary_tsv",
    "export_limma_assay_matrix_tsv",
    "export_limma_contrast_matrix_tsv",
    "export_limma_design_matrix_tsv",
    "export_limma_sample_annotations_tsv",
    "export_msstats_compatible_input_tsv",
    "export_multi_condition_differential_abundance_tsv",
    "export_multi_contrast_consistency_tsv",
    "export_multiplex_channel_assignment_tsv",
    "export_multiplex_duplicate_assignment_tsv",
    "export_multiplex_metadata_summary_tsv",
    "export_multiplex_missing_condition_tsv",
    "export_peptide_protein_table_tsv",
    "export_peptides_fasta",
    "export_peptides_jsonl",
    "export_peptides_parquet",
    "export_peptides_tsv",
    "export_power_effect_size_grid_tsv",
    "export_power_estimation_summary_tsv",
    "export_power_variance_tsv",
    "export_psm_jsonl",
    "export_psm_tsv",
    "export_ptm_differential_volcano_tsv",
    "export_ptm_mapped_site_annotation_tsv",
    "export_ptm_phosphosite_motif_enriched_term_tsv",
    "export_ptm_phosphosite_motif_frequency_tsv",
    "export_ptm_phosphosite_motif_logo_tsv",
    "export_ptm_phosphosite_motif_window_tsv",
    "export_ptm_regulator_enrichment_summary_tsv",
    "export_ptm_regulator_enrichment_tsv",
    "export_ptm_site_annotation_biology_tsv",
    "export_ptm_site_annotation_mapping_summary_tsv",
    "export_ptm_site_context_summary_tsv",
    "export_ptm_site_context_tsv",
    "export_ptm_site_differential_broken_pairs_tsv",
    "export_ptm_site_differential_tsv",
    "export_ptm_unmapped_site_annotation_tsv",
    "export_quant_design_contrast_estimates_tsv",
    "export_quant_design_matrix_tsv",
    "export_quant_design_model_coefficients_tsv",
    "export_sample_cluster_tsv",
    "export_sample_correlation_tsv",
    "export_sample_distance_tsv",
    "export_sample_exploration_summary_tsv",
    "export_sample_outlier_tsv",
    "export_sample_pca_scores_tsv",
    "export_sample_pca_variance_tsv",
    "export_sample_sheet_repair_suggestions_tsv",
    "export_silac_peptide_ratio_tsv",
    "export_silac_protein_ratio_tsv",
    "export_silac_ratio_summary_tsv",
    "export_silac_validation_distribution_tsv",
    "export_silac_validation_label_tsv",
    "export_silac_validation_summary_tsv",
    "export_silac_validation_weak_tsv",
    "export_spectra_jsonl",
    "export_spectrum_peak_match_tsv",
    "export_spectrum_unmatched_peak_tsv",
    "export_time_course_differential_tsv",
    "export_tmt_channel_distribution_tsv",
    "export_tmt_channel_mapping_tsv",
    "export_tmt_channel_totals_tsv",
    "export_tmt_filtered_interference_tsv",
    "export_tmt_integrated_protein_matrix_tsv",
    "export_tmt_interference_channel_summary_tsv",
    "export_tmt_interference_observation_tsv",
    "export_tmt_interference_summary_tsv",
    "export_tmt_normalization_summary_tsv",
    "export_tmt_normalization_transform_tsv",
    "export_tmt_normalized_peptide_matrix_tsv",
    "export_tmt_normalized_protein_matrix_tsv",
    "export_tmt_peptide_matrix_tsv",
    "export_tmt_peptide_ratio_tsv",
    "export_tmt_plex_alignment_tsv",
    "export_tmt_plex_effect_tsv",
    "export_tmt_plex_integration_summary_tsv",
    "export_tmt_protein_matrix_tsv",
    "export_tmt_protein_ratio_tsv",
    "export_tmt_ratio_summary_tsv",
    "export_tmt_report_summary_tsv",
    "export_tmt_validation_channel_tsv",
    "export_tmt_validation_distribution_tsv",
    "export_tmt_validation_summary_tsv",
    "export_tmt_validation_weak_tsv",
    "export_volcano_review_html",
    "export_volcano_review_json",
    "export_volcano_review_svg",
    "extract_mzml_chromatograms",
    "extract_mzml_chromatographic_evidence",
    "extract_mzml_chromatographic_peaks",
    "extract_mzml_dia_fragment_trace_coelution",
    "extract_mzml_precursor_isotope_fit",
    "extract_mzml_raw_signal_evidence_cards",
    "extract_mzml_retention_time_alignment",
    "extract_mzml_xic_traces",
    "filter_fasta_records",
    "filter_psms_by_fdr",
    "find_spectral_library_candidates",
    "fit_quant_design_matrix_model",
    "format_failure_explanation_for_cli",
    "generate_decoy_records",
    "get_modification",
    "get_search_adapter_manifest",
    "hashlib",
    "import_spectral_library",
    "impute_label_free_table",
    "infer_proteins_by_parsimony",
    "json",
    "load_modification_registry",
    "load_qc_threshold_policy",
    "map_ptm_evidence_to_protein_sites",
    "normalize_label_free_table",
    "normalize_search_results_with_adapter",
    "parse_biological_context_table",
    "parse_complex_membership_table",
    "parse_experimental_design_table",
    "parse_fasta_document",
    "parse_go_annotation_table",
    "parse_lab_protocol_context_table",
    "parse_limma_result_table",
    "parse_mgf",
    "parse_ms1_feature_table",
    "parse_msstats_result_table",
    "parse_mzml",
    "parse_ortholog_table",
    "parse_pathway_membership_table",
    "parse_ppi_edge_table",
    "parse_precursor_intensity_table",
    "parse_protein_annotation_table",
    "parse_protein_reference_table",
    "parse_protein_set_table",
    "parse_psm_tsv",
    "parse_ptm_localization_tsv",
    "parse_ptm_peptide",
    "parse_ptm_peptide_tsv",
    "parse_ptm_site_annotation_tsv",
    "parse_ptm_site_context_tsv",
    "parse_regulator_evidence_table",
    "parse_regulator_site_signal_table",
    "parse_search_parameter_file",
    "parse_silac_feature_table",
    "parse_tmt_reporter_table",
    "peptide_export_fingerprint",
    "predict_peptide_isotope_envelopes",
    "program_summary",
    "render_analysis_recommendation_summary_tsv",
    "render_analysis_recommendation_tsv",
    "render_belief_audit_html",
    "render_belief_audit_summary_tsv",
    "render_belief_audit_tsv",
    "render_biological_context_mapping_summary_tsv",
    "render_biological_context_mapping_tsv",
    "render_biological_context_term_tsv",
    "render_biomarker_candidate_ranking_summary_tsv",
    "render_biomarker_candidate_ranking_tsv",
    "render_biomarker_stability_candidate_tsv",
    "render_biomarker_stability_subgroup_tsv",
    "render_biomarker_stability_summary_tsv",
    "render_biomarker_stability_tsv",
    "render_chimeric_spectrum_competing_evidence_tsv",
    "render_chimeric_spectrum_spectra_tsv",
    "render_chromatographic_peaks_tsv",
    "render_chromatographic_peptide_evidence_tsv",
    "render_chromatographic_target_evidence_tsv",
    "render_comet_canonical_psm_tsv",
    "render_comet_psm_tsv",
    "render_comet_summary_tsv",
    "render_compact_result_summary_entry_tsv",
    "render_compact_result_summary_markdown",
    "render_compact_result_summary_overview_tsv",
    "render_compartment_activity_condition_comparison_tsv",
    "render_compartment_activity_condition_score_tsv",
    "render_compartment_activity_matrix_tsv",
    "render_compartment_activity_sample_score_tsv",
    "render_compartment_activity_unresolved_member_tsv",
    "render_compartment_biology_summary_tsv",
    "render_compartment_enrichment_tsv",
    "render_complex_activity_condition_comparison_tsv",
    "render_complex_activity_condition_score_tsv",
    "render_complex_activity_matrix_tsv",
    "render_complex_activity_sample_score_tsv",
    "render_complex_activity_summary_tsv",
    "render_complex_activity_unresolved_member_tsv",
    "render_complex_enrichment_entry_tsv",
    "render_complex_enrichment_summary_tsv",
    "render_complex_member_contribution_tsv",
    "render_complex_unresolved_member_tsv",
    "render_contaminant_burden_tsv",
    "render_contaminant_proteins_tsv",
    "render_cross_run_reproducibility_entries_tsv",
    "render_cross_run_reproducibility_summary_tsv",
    "render_dia_fragment_coelution_fragments_tsv",
    "render_dia_fragment_coelution_runs_tsv",
    "render_dia_library_coverage_condition_tsv",
    "render_dia_library_coverage_observed_outside_peptide_tsv",
    "render_dia_library_coverage_observed_outside_protein_tsv",
    "render_dia_library_coverage_peptide_tsv",
    "render_dia_library_coverage_protein_tsv",
    "render_dia_library_coverage_sample_tsv",
    "render_dia_library_coverage_summary_tsv",
    "render_dia_peptide_quantity_matrix_tsv",
    "render_dia_precursor_matrix_summary_tsv",
    "render_dia_precursor_metadata_tsv",
    "render_dia_precursor_q_value_matrix_tsv",
    "render_dia_precursor_quantity_matrix_tsv",
    "render_dia_protein_matrix_summary_tsv",
    "render_dia_protein_quantity_matrix_tsv",
    "render_dia_protein_rollup_evidence_tsv",
    "render_dia_run_qc_correlation_tsv",
    "render_dia_run_qc_intensity_distribution_tsv",
    "render_dia_run_qc_outlier_tsv",
    "render_dia_run_qc_run_table_tsv",
    "render_dia_run_qc_summary_tsv",
    "render_diann_precursor_tsv",
    "render_diann_protein_group_tsv",
    "render_diann_summary_tsv",
    "render_discovery_targeted_peptide_selection_rejected_tsv",
    "render_discovery_targeted_peptide_selection_selected_tsv",
    "render_discovery_targeted_peptide_selection_summary_tsv",
    "render_disease_phenotype_interpretation_summary_tsv",
    "render_disease_phenotype_interpretation_tsv",
    "render_drug_target_interpretation_summary_tsv",
    "render_drug_target_interpretation_tsv",
    "render_evidence_level_fdr_entries_tsv",
    "render_evidence_level_fdr_summary_tsv",
    "render_experiment_feasibility_group_sizes_tsv",
    "render_experiment_feasibility_invalid_contrasts_tsv",
    "render_experiment_feasibility_missing_metadata_tsv",
    "render_experiment_feasibility_model_support_tsv",
    "render_experiment_feasibility_valid_contrasts_tsv",
    "render_failure_explanation_summary_tsv",
    "render_failure_explanation_tsv",
    "render_fasta_profile_invalid_sequence_tsv",
    "render_fasta_profile_length_distribution_tsv",
    "render_fasta_profile_organism_distribution_tsv",
    "render_fasta_profile_summary_tsv",
    "render_fragment_ion_report_tsv",
    "render_fragment_ratio_stability_fragments_tsv",
    "render_fragment_ratio_stability_observations_tsv",
    "render_fragpipe_benchmark_summary_tsv",
    "render_fragpipe_canonical_psm_tsv",
    "render_fragpipe_count_comparisons_tsv",
    "render_fragpipe_open_search_evidence_tsv",
    "render_fragpipe_peptide_tsv",
    "render_fragpipe_protein_group_comparison_tsv",
    "render_fragpipe_protein_quantity_tsv",
    "render_fragpipe_protein_tsv",
    "render_fragpipe_psm_tsv",
    "render_fragpipe_q_value_comparison_tsv",
    "render_fragpipe_summary_tsv",
    "render_generic_psm_mapper_tsv",
    "render_go_enrichment_summary_tsv",
    "render_go_enrichment_term_tsv",
    "render_go_enrichment_unannotated_tsv",
    "render_isotope_envelopes_tsv",
    "render_mapped_ortholog_tsv",
    "render_maxquant_evidence_tsv",
    "render_maxquant_lfq_candidate_tsv",
    "render_maxquant_peptide_tsv",
    "render_maxquant_protein_group_tsv",
    "render_maxquant_summary_tsv",
    "render_openms_feature_tsv",
    "render_openms_protein_tsv",
    "render_openms_psm_tsv",
    "render_openms_summary_tsv",
    "render_ortholog_mapping_summary_tsv",
    "render_panel_redundancy_candidate_tsv",
    "render_panel_redundancy_cluster_tsv",
    "render_panel_redundancy_dropped_tsv",
    "render_panel_redundancy_summary_tsv",
    "render_parsimony_review_ambiguities_tsv",
    "render_parsimony_review_proteins_tsv",
    "render_parsimony_review_summary_tsv",
    "render_pathway_activity_condition_comparison_tsv",
    "render_pathway_activity_condition_score_tsv",
    "render_pathway_activity_matrix_tsv",
    "render_pathway_activity_sample_score_tsv",
    "render_pathway_activity_summary_tsv",
    "render_pathway_activity_unresolved_member_tsv",
    "render_pathway_enrichment_entry_tsv",
    "render_pathway_enrichment_summary_tsv",
    "render_pathway_member_contribution_tsv",
    "render_pathway_unresolved_member_tsv",
    "render_peptide_detectability_tsv",
    "render_peptide_evidence_entries_tsv",
    "render_peptide_evidence_summary_tsv",
    "render_peptide_intensity_aggregation_tsv",
    "render_peptide_intensity_matrix_summary_tsv",
    "render_peptide_intensity_matrix_tsv",
    "render_peptide_intensity_missingness_mask_tsv",
    "render_peptide_intensity_missingness_tsv",
    "render_peptide_profile_inconsistency_tsv",
    "render_picked_protein_fdr_entries_tsv",
    "render_picked_protein_fdr_summary_tsv",
    "render_ppi_isolated_protein_tsv",
    "render_ppi_module_enrichment_tsv",
    "render_ppi_module_tsv",
    "render_ppi_network_edge_tsv",
    "render_ppi_network_module_summary_tsv",
    "render_precursor_isotope_fit_entries_tsv",
    "render_precursor_isotope_fit_peaks_tsv",
    "render_precursor_isotope_fit_summary_tsv",
    "render_precursor_mass_error_distribution_tsv",
    "render_precursor_mass_error_observations_tsv",
    "render_precursor_mass_error_summary_tsv",
    "render_protein_ambiguity_entries_tsv",
    "render_protein_ambiguity_summary_tsv",
    "render_protein_annotation_summary_tsv",
    "render_protein_annotation_tsv",
    "render_protein_coverage_entries_tsv",
    "render_protein_coverage_peptide_coordinates_tsv",
    "render_protein_coverage_plot_html",
    "render_protein_coverage_plot_positions_tsv",
    "render_protein_coverage_plot_svg",
    "render_protein_coverage_regions_tsv",
    "render_protein_coverage_summary_tsv",
    "render_protein_coverage_uncovered_regions_tsv",
    "render_protein_evidence_entries_tsv",
    "render_protein_evidence_summary_tsv",
    "render_protein_grouping_entries_tsv",
    "render_protein_grouping_summary_tsv",
    "render_protein_inference_benchmark_assessments_tsv",
    "render_protein_inference_benchmark_scenarios_tsv",
    "render_protein_inference_benchmark_summary_tsv",
    "render_protein_intensity_matrix_summary_tsv",
    "render_protein_intensity_matrix_tsv",
    "render_protein_intensity_missingness_tsv",
    "render_protein_lfq_disconnected_components_tsv",
    "render_protein_lfq_matrix_tsv",
    "render_protein_lfq_missingness_tsv",
    "render_protein_lfq_pairwise_ratios_tsv",
    "render_protein_lfq_summary_tsv",
    "render_protein_peptide_contribution_tsv",
    "render_protein_set_condition_comparison_tsv",
    "render_protein_set_condition_score_tsv",
    "render_protein_set_enrichment_summary_tsv",
    "render_protein_set_enrichment_tsv",
    "render_protein_set_sample_score_tsv",
    "render_protein_set_score_matrix_tsv",
    "render_protein_set_scoring_summary_tsv",
    "render_protein_set_universe_gap_tsv",
    "render_protein_set_unresolved_member_tsv",
    "render_protocol_consistency_tsv",
    "render_psm_error_rate_annotation_summary_tsv",
    "render_psm_error_rate_annotation_tsv",
    "render_psm_evidence_inspection_summary_tsv",
    "render_psm_inspection_distribution_tsv",
    "render_psm_target_decoy_fdr_summary_tsv",
    "render_psm_target_decoy_fdr_tsv",
    "render_ptm_ambiguity_review_summary_tsv",
    "render_ptm_coordinate_validation_tsv",
    "render_ptm_evidence_site_candidate_tsv",
    "render_ptm_localization_scoring_entry_tsv",
    "render_ptm_localization_scoring_summary_tsv",
    "render_ptm_localized_site_review_tsv",
    "render_ptm_occupancy_counterpart_tsv",
    "render_ptm_peptide_record_tsv",
    "render_ptm_peptide_rejected_tsv",
    "render_ptm_peptide_site_tsv",
    "render_ptm_peptide_summary_tsv",
    "render_ptm_protein_site_mapping_tsv",
    "render_ptm_site_coverage_tsv",
    "render_ptm_site_group_quant_matrix_tsv",
    "render_ptm_site_group_quant_missingness_tsv",
    "render_ptm_site_group_quant_summary_tsv",
    "render_ptm_site_occupancy_entry_tsv",
    "render_ptm_site_occupancy_summary_tsv",
    "render_ptm_site_quant_excluded_tsv",
    "render_ptm_site_quant_matrix_tsv",
    "render_ptm_site_quant_missingness_tsv",
    "render_ptm_site_quant_summary_tsv",
    "render_ptm_site_table_tsv",
    "render_ptm_unlocalized_group_review_tsv",
    "render_ptm_unmapped_peptide_tsv",
    "render_qc_assessment_html",
    "render_qc_assessment_tsv",
    "render_raw_signal_evidence_card_summary_tsv",
    "render_raw_signal_evidence_card_tsv",
    "render_raw_signal_evidence_cards_html",
    "render_records_fasta",
    "render_regulator_inference_summary_tsv",
    "render_regulator_inference_tsv",
    "render_rejected_biological_context_tsv",
    "render_rejected_complex_membership_tsv",
    "render_rejected_evidence_tsv",
    "render_rejected_go_annotation_tsv",
    "render_rejected_ortholog_tsv",
    "render_rejected_pathway_membership_tsv",
    "render_rejected_ppi_edge_tsv",
    "render_rejected_protein_annotation_tsv",
    "render_rejected_protein_reference_tsv",
    "render_rejected_protein_set_membership_tsv",
    "render_rejected_protein_set_tsv",
    "render_rejected_regulator_evidence_tsv",
    "render_rejected_regulator_site_signal_tsv",
    "render_result_explanation_evidence_tsv",
    "render_result_explanation_summary_tsv",
    "render_result_explanation_tsv",
    "render_result_query_answer_tsv",
    "render_result_query_evidence_tsv",
    "render_result_query_summary_tsv",
    "render_retention_time_alignment_failed_anchors_tsv",
    "render_retention_time_alignment_models_tsv",
    "render_retention_time_alignment_residuals_tsv",
    "render_sage_canonical_psm_tsv",
    "render_sage_psm_tsv",
    "render_sage_summary_tsv",
    "render_score_separation_bins_tsv",
    "render_score_separation_summary_tsv",
    "render_spectral_library_candidates_tsv",
    "render_spectral_library_search_tsv",
    "render_spectral_library_summary_tsv",
    "render_spectronaut_precursor_quantity_tsv",
    "render_spectronaut_precursor_tsv",
    "render_spectronaut_protein_group_quantity_tsv",
    "render_spectronaut_protein_group_tsv",
    "render_spectronaut_summary_tsv",
    "render_spectrum_distribution_tsv",
    "render_spectrum_run_qc_distribution_tsv",
    "render_spectrum_run_qc_flagged_spectra_tsv",
    "render_spectrum_run_qc_spectra_tsv",
    "render_spectrum_run_qc_summary_tsv",
    "render_spectrum_run_qc_time_bins_tsv",
    "render_spectrum_run_qc_trace_tsv",
    "render_spectrum_similarity_tsv",
    "render_spectrum_summary_tsv",
    "render_target_decoy_reference_entries_tsv",
    "render_target_decoy_reference_summary_tsv",
    "render_target_panel_intensity_tsv",
    "render_target_panel_matrix_tsv",
    "render_target_panel_missing_tsv",
    "render_target_panel_summary_tsv",
    "render_target_panel_target_tsv",
    "render_targeted_assay_interference_assay_tsv",
    "render_targeted_assay_interference_panel_tsv",
    "render_targeted_assay_interference_summary_tsv",
    "render_targeted_assay_interference_transition_tsv",
    "render_targeted_assay_qc_coelution_tsv",
    "render_targeted_assay_qc_fragment_ratio_tsv",
    "render_targeted_assay_qc_replicate_cv_tsv",
    "render_targeted_assay_qc_retention_tsv",
    "render_targeted_assay_qc_summary_tsv",
    "render_targeted_assay_qc_target_tsv",
    "render_targeted_assay_qc_transition_coelution_tsv",
    "render_targeted_assay_qc_transition_qc_tsv",
    "render_targeted_assay_qc_transition_tsv",
    "render_targeted_assay_qc_unreliable_tsv",
    "render_targeted_carryover_candidates_tsv",
    "render_targeted_carryover_summary_tsv",
    "render_targeted_matrix_excluded_transition_tsv",
    "render_targeted_matrix_flagged_tsv",
    "render_targeted_matrix_missingness_tsv",
    "render_targeted_matrix_retained_transition_tsv",
    "render_targeted_matrix_sample_tsv",
    "render_targeted_matrix_summary_tsv",
    "render_targeted_matrix_target_tsv",
    "render_targeted_panel_design_assay_tsv",
    "render_targeted_panel_design_omitted_candidate_tsv",
    "render_targeted_panel_design_panel_tsv",
    "render_targeted_panel_design_summary_tsv",
    "render_targeted_result_observation_tsv",
    "render_targeted_result_validation_evidence_tsv",
    "render_targeted_result_validation_summary_tsv",
    "render_targeted_result_validation_tsv",
    "render_targeted_transition_selection_rejected_tsv",
    "render_targeted_transition_selection_selected_tsv",
    "render_targeted_transition_selection_summary_tsv",
    "render_transition_qc_sample_tsv",
    "render_transition_qc_summary_tsv",
    "render_transition_qc_transition_tsv",
    "render_transition_qc_weak_tsv",
    "render_unknown_compartment_localization_tsv",
    "render_unknown_disease_phenotype_annotation_tsv",
    "render_unmapped_biological_context_tsv",
    "render_unmapped_ortholog_tsv",
    "render_unmapped_protein_annotation_tsv",
    "render_unresolved_regulator_target_tsv",
    "render_validation_evidence_card_assay_tsv",
    "render_validation_evidence_card_summary_tsv",
    "render_validation_evidence_card_tsv",
    "render_validation_evidence_card_warning_tsv",
    "render_validation_experiment_planning_plan_tsv",
    "render_validation_experiment_planning_summary_tsv",
    "render_validation_experiment_planning_warning_tsv",
    "render_xic_traces_tsv",
    "require_single_lab_protocol_context",
    "resolve_protease_rule",
    "score_chimeric_spectra_from_psms",
    "score_dia_fragment_ratio_stability",
    "search_spectral_library",
    "sequence_checksum",
    "summarize_missing_values",
    "time",
    "validate_proteomics_input",
    "validate_ptm_site_coordinates",
    "validate_search_parameters",
    "validate_target_decoy_database",
    "write_theoretical_digest_bundle",
]
