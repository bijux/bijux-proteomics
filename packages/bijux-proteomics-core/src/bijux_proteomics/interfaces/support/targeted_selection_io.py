# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Targeted-selection input loaders shared by CLI command modules."""

from __future__ import annotations

from .imports import *  # noqa: F401,F403

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
        return parse_mgf(input_path).accepted_spectra
    if resolved_kind == "mzml":
        return parse_mzml(input_path).accepted_spectra
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

def _load_targeted_selection_targets(path: Path) -> tuple[DiscoveryTargetProteinEntry, ...]:
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
                        protein_refs=_split_semicolon_field(row.get("protein_refs", "")),
                        gene_symbol=(
                            gene_symbol if (gene_symbol := str(row.get("gene_symbol", "")).strip()) else None
                        ),
                        discovery_peptides=_split_semicolon_field(row.get("peptides", "")),
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
                        peptide_q_value=float(str(row.get("peptide_q_value", "")).strip()),
                        accepted=_parse_cli_bool(row.get("accepted", ""), field_name="accepted"),
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
                        protein_refs=_split_semicolon_field(row.get("protein_refs", "")),
                        target_decoy_label=TargetDecoyLabel(
                            str(row.get("target_decoy_label", "")).strip()
                        ),
                        target_decoy_contaminant_class=TargetDecoyContaminantClass(
                            str(
                                row.get("target_decoy_contaminant_class", "")
                            ).strip()
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
                        canonical_peptide=str(
                            row.get("canonical_peptide", "")
                        ).strip(),
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
                            else float(str(row.get("replicate_consistency", "")).strip())
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
        entries_by_assay: dict[str, dict[str, object]] = {}
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
                        "precursor_mz": float(
                            str(row.get("precursor_mz", "")).strip()
                        ),
                        "source_library_entry_id": (
                            value
                            if (value := str(row.get("source_library_entry_id", "")).strip())
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
                assert isinstance(selected_transitions, list)
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
                        fragment_sequence=str(
                            row.get("fragment_sequence", "")
                        ).strip(),
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
        selected_transitions = tuple(
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
                selected_transition_count=assay_payload[
                    "selected_transition_count"
                ],
                sufficient_transition_support=assay_payload[
                    "sufficient_transition_support"
                ],
                instrument_caveats=assay_payload["instrument_caveats"],
                selected_transitions=selected_transitions,
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

__all__ = [name for name in globals() if not name.startswith("__")]
