# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Targeted peptide, transition, and biomarker selection Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    SpectralLibraryEntry,
    SpectralLibraryFormat,
    build_spectral_library_summary,
    import_spectral_library,
)
from bijux_proteomics.interfaces.support.multiplex_targeted import (
    build_discovery_targeted_peptide_selection_report,
    build_targeted_assay_interference_report,
    build_targeted_transition_selection_report,
    render_discovery_targeted_peptide_selection_rejected_tsv,
    render_discovery_targeted_peptide_selection_selected_tsv,
    render_discovery_targeted_peptide_selection_summary_tsv,
    render_targeted_assay_interference_assay_tsv,
    render_targeted_assay_interference_panel_tsv,
    render_targeted_assay_interference_summary_tsv,
    render_targeted_assay_interference_transition_tsv,
    render_targeted_transition_selection_rejected_tsv,
    render_targeted_transition_selection_selected_tsv,
    render_targeted_transition_selection_summary_tsv,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    BiomarkerCandidateRankingInput,
    FastaParseMode,
    build_biomarker_candidate_ranking_report,
    render_biomarker_candidate_ranking_summary_tsv,
    render_biomarker_candidate_ranking_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.sequence_support.fasta_inputs import (
    _load_fasta_report,
)
from bijux_proteomics.interfaces.support.targeted_selection_io.protein_support import (
    _load_assay_interference_support_by_protein,
    _load_selected_peptide_support_by_protein,
)
from bijux_proteomics.interfaces.support.targeted_selection_io.selection_tables import (
    _load_peptide_evidence_entries,
    _load_selected_targeted_peptides,
    _load_selected_targeted_transitions,
    _load_targeted_selection_targets,
)
from bijux_proteomics.interfaces.support.biomarker_candidate_support.biological_candidates import (
    _build_biomarker_candidates_from_biological_report_dir,
)
from bijux_proteomics.interfaces.support.biomarker_candidate_support.ptm_candidates import (
    _build_biomarker_candidates_from_ptm_report_dir,
)


def run_targeted_peptide_selection_command(
    protein_card_tsv: Path,
    peptide_evidence_tsv: Path,
    input_fasta: Path,
    protease: str,
    missed_cleavages: int,
    top_peptides_per_target: int,
    summary_tsv_out: Path | None,
    selected_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if missed_cleavages < 0:
        raise click.ClickException("missed-cleavages must be non-negative")
    if top_peptides_per_target < 1:
        raise click.ClickException("top-peptides-per-target must be at least 1")

    targets = _load_targeted_selection_targets(protein_card_tsv)
    peptide_evidence_entries = _load_peptide_evidence_entries(peptide_evidence_tsv)
    fasta_report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode.STRICT,
        allow_rejected=False,
    )

    try:
        report = build_discovery_targeted_peptide_selection_report(
            targets,
            peptide_evidence_entries,
            fasta_report.accepted_records,
            protease=protease,
            missed_cleavages=missed_cleavages,
            top_peptides_per_target=top_peptides_per_target,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_discovery_targeted_peptide_selection_summary_tsv(report),
        )
    if selected_tsv_out is not None:
        _write_text_output(
            selected_tsv_out,
            render_discovery_targeted_peptide_selection_selected_tsv(report),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_discovery_targeted_peptide_selection_rejected_tsv(report),
        )

    payload = {
        "protease": report.protease,
        "missed_cleavages": report.missed_cleavages,
        "top_peptides_per_target": report.top_peptides_per_target,
        "target_count": len(targets),
        "peptide_evidence_count": len(peptide_evidence_entries),
        "fasta_summary": {
            "accepted_record_count": len(fasta_report.accepted_records),
            "rejected_record_count": len(fasta_report.rejected_records),
        },
        "selection_summary": report.summary.to_dict(),
        "selected_entries": [entry.to_dict() for entry in report.selected_entries],
        "rejected_candidates": [
            entry.to_dict() for entry in report.rejected_candidates
        ],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "selected_tsv": (
                None if selected_tsv_out is None else str(selected_tsv_out)
            ),
            "rejected_tsv": (
                None if rejected_tsv_out is None else str(rejected_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_targeted_transition_selection_command(
    selected_peptide_tsv: Path,
    spectral_library_path: Path | None,
    spectral_library_format: str | None,
    default_precursor_charge: int,
    fragment_charges: tuple[int, ...],
    min_transitions_per_peptide: int,
    max_transitions_per_peptide: int,
    min_fragment_mz: float,
    max_fragment_mz: float,
    precursor_exclusion_da: float,
    library_match_tolerance_da: float,
    summary_tsv_out: Path | None,
    selected_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if default_precursor_charge < 1:
        raise click.ClickException("default-precursor-charge must be at least 1")
    if not fragment_charges:
        raise click.ClickException("at least one fragment-charge must be provided")
    if any(charge < 1 for charge in fragment_charges):
        raise click.ClickException("fragment-charge values must all be at least 1")
    if min_transitions_per_peptide < 1:
        raise click.ClickException("min-transitions-per-peptide must be at least 1")
    if max_transitions_per_peptide < min_transitions_per_peptide:
        raise click.ClickException(
            "max-transitions-per-peptide must be greater than or equal to min-transitions-per-peptide"
        )
    if min_fragment_mz <= 0.0:
        raise click.ClickException("min-fragment-mz must be greater than zero")
    if max_fragment_mz <= min_fragment_mz:
        raise click.ClickException(
            "max-fragment-mz must be greater than min-fragment-mz"
        )
    if precursor_exclusion_da <= 0.0:
        raise click.ClickException("precursor-exclusion-da must be greater than zero")
    if library_match_tolerance_da <= 0.0:
        raise click.ClickException(
            "library-match-tolerance-da must be greater than zero"
        )

    selected_peptides = _load_selected_targeted_peptides(selected_peptide_tsv)
    spectral_library_entries: tuple[SpectralLibraryEntry, ...] = ()
    spectral_library_summary: dict[str, object] | None = None
    if spectral_library_path is not None:
        import_report = import_spectral_library(
            spectral_library_path,
            library_format=(
                None
                if spectral_library_format is None
                else SpectralLibraryFormat(spectral_library_format)
            ),
        )
        spectral_library_entries = import_report.entries
        summary = build_spectral_library_summary(import_report)
        spectral_library_summary = {
            "source_path": str(spectral_library_path),
            "source_format": import_report.source_format.value,
            "accepted_entry_count": import_report.accepted_entry_count,
            "rejected_entry_count": import_report.rejected_entry_count,
            "summary": summary.to_dict(),
        }

    try:
        report = build_targeted_transition_selection_report(
            selected_peptides,
            spectral_library_entries=spectral_library_entries,
            default_precursor_charge=default_precursor_charge,
            fragment_charges=fragment_charges,
            minimum_transition_count=min_transitions_per_peptide,
            maximum_transition_count=max_transitions_per_peptide,
            minimum_fragment_mz=min_fragment_mz,
            maximum_fragment_mz=max_fragment_mz,
            precursor_exclusion_da=precursor_exclusion_da,
            library_match_tolerance_da=library_match_tolerance_da,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_targeted_transition_selection_summary_tsv(report),
        )
    if selected_tsv_out is not None:
        _write_text_output(
            selected_tsv_out,
            render_targeted_transition_selection_selected_tsv(report),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_targeted_transition_selection_rejected_tsv(report),
        )

    payload = {
        "selected_peptide_count": len(selected_peptides),
        "spectral_library": spectral_library_summary,
        "default_precursor_charge": default_precursor_charge,
        "fragment_charges": list(fragment_charges),
        "minimum_transition_count": report.minimum_transition_count,
        "maximum_transition_count": report.maximum_transition_count,
        "minimum_fragment_mz": report.minimum_fragment_mz,
        "maximum_fragment_mz": report.maximum_fragment_mz,
        "precursor_exclusion_da": report.precursor_exclusion_da,
        "library_match_tolerance_da": report.library_match_tolerance_da,
        "selection_summary": report.summary.to_dict(),
        "peptide_entries": [entry.to_dict() for entry in report.peptide_entries],
        "rejected_transitions": [
            entry.to_dict() for entry in report.rejected_transitions
        ],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "selected_tsv": (
                None if selected_tsv_out is None else str(selected_tsv_out)
            ),
            "rejected_tsv": (
                None if rejected_tsv_out is None else str(rejected_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_targeted_assay_interference_command(
    selected_peptide_tsv: Path,
    selected_transition_tsv: Path,
    input_fasta: Path,
    spectral_library_path: Path | None,
    spectral_library_format: str | None,
    protease: str,
    missed_cleavages: int,
    precursor_tolerance_da: float,
    fragment_tolerance_da: float,
    coelution_rt_window_minutes: float,
    min_export_transitions: int,
    summary_tsv_out: Path | None,
    assay_tsv_out: Path | None,
    transition_tsv_out: Path | None,
    panel_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if missed_cleavages < 0:
        raise click.ClickException("missed-cleavages must be non-negative")
    if precursor_tolerance_da <= 0.0:
        raise click.ClickException("precursor-tolerance-da must be greater than zero")
    if fragment_tolerance_da <= 0.0:
        raise click.ClickException("fragment-tolerance-da must be greater than zero")
    if coelution_rt_window_minutes <= 0.0:
        raise click.ClickException(
            "coelution-rt-window-minutes must be greater than zero"
        )
    if min_export_transitions < 1:
        raise click.ClickException("min-export-transitions must be at least 1")

    selected_peptides = _load_selected_targeted_peptides(selected_peptide_tsv)
    selected_transition_entries = _load_selected_targeted_transitions(
        selected_transition_tsv
    )
    fasta_report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode.STRICT,
        allow_rejected=False,
    )
    spectral_library_entries: tuple[SpectralLibraryEntry, ...] = ()
    spectral_library_summary: dict[str, object] | None = None
    if spectral_library_path is not None:
        import_report = import_spectral_library(
            spectral_library_path,
            library_format=(
                None
                if spectral_library_format is None
                else SpectralLibraryFormat(spectral_library_format)
            ),
        )
        spectral_library_entries = import_report.entries
        summary = build_spectral_library_summary(import_report)
        spectral_library_summary = {
            "source_path": str(spectral_library_path),
            "source_format": import_report.source_format.value,
            "accepted_entry_count": import_report.accepted_entry_count,
            "rejected_entry_count": import_report.rejected_entry_count,
            "summary": summary.to_dict(),
        }

    try:
        report = build_targeted_assay_interference_report(
            selected_peptides,
            selected_transition_entries,
            fasta_report.accepted_records,
            spectral_library_entries=spectral_library_entries,
            protease=protease,
            missed_cleavages=missed_cleavages,
            precursor_tolerance_da=precursor_tolerance_da,
            fragment_tolerance_da=fragment_tolerance_da,
            coelution_rt_window_minutes=coelution_rt_window_minutes,
            minimum_export_transitions=min_export_transitions,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_targeted_assay_interference_summary_tsv(report),
        )
    if assay_tsv_out is not None:
        _write_text_output(
            assay_tsv_out,
            render_targeted_assay_interference_assay_tsv(report),
        )
    if transition_tsv_out is not None:
        _write_text_output(
            transition_tsv_out,
            render_targeted_assay_interference_transition_tsv(report),
        )
    if panel_tsv_out is not None:
        _write_text_output(
            panel_tsv_out,
            render_targeted_assay_interference_panel_tsv(report),
        )

    payload = {
        "selected_peptide_count": len(selected_peptides),
        "selected_transition_assay_count": len(selected_transition_entries),
        "spectral_library": spectral_library_summary,
        "fasta_summary": {
            "accepted_record_count": len(fasta_report.accepted_records),
            "rejected_record_count": len(fasta_report.rejected_records),
        },
        "protease": report.protease,
        "missed_cleavages": report.missed_cleavages,
        "precursor_tolerance_da": report.precursor_tolerance_da,
        "fragment_tolerance_da": report.fragment_tolerance_da,
        "coelution_rt_window_minutes": report.coelution_rt_window_minutes,
        "minimum_export_transitions": report.minimum_export_transitions,
        "interference_summary": report.summary.to_dict(),
        "assay_entries": [entry.to_dict() for entry in report.assay_entries],
        "transition_entries": [entry.to_dict() for entry in report.transition_entries],
        "panel_entries": [entry.to_dict() for entry in report.panel_entries],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "assay_tsv": None if assay_tsv_out is None else str(assay_tsv_out),
            "transition_tsv": (
                None if transition_tsv_out is None else str(transition_tsv_out)
            ),
            "panel_tsv": None if panel_tsv_out is None else str(panel_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_biomarker_candidate_ranking_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    selected_peptide_tsv: Path | None,
    assay_interference_assay_tsv: Path | None,
    summary_tsv_out: Path | None,
    candidate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if biological_report_dir is None and ptm_report_dir is None:
        raise click.ClickException(
            "at least one of --biological-report-dir or --ptm-report-dir must be provided"
        )

    selected_peptide_support = (
        None
        if selected_peptide_tsv is None
        else _load_selected_peptide_support_by_protein(selected_peptide_tsv)
    )
    assay_interference_support = (
        None
        if assay_interference_assay_tsv is None
        else _load_assay_interference_support_by_protein(assay_interference_assay_tsv)
    )

    candidates: list[BiomarkerCandidateRankingInput] = []
    biological_sample_qc_score: float | None = None
    if biological_report_dir is not None:
        biological_candidates, biological_sample_qc_score = (
            _build_biomarker_candidates_from_biological_report_dir(
                biological_report_dir,
                selected_peptide_support=selected_peptide_support,
                assay_interference_support=assay_interference_support,
            )
        )
        candidates.extend(biological_candidates)
    if ptm_report_dir is not None:
        candidates.extend(
            _build_biomarker_candidates_from_ptm_report_dir(
                ptm_report_dir,
                sample_qc_score=biological_sample_qc_score,
            )
        )

    try:
        report = build_biomarker_candidate_ranking_report(tuple(candidates))
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_biomarker_candidate_ranking_summary_tsv(report),
        )
    if candidate_tsv_out is not None:
        _write_text_output(
            candidate_tsv_out,
            render_biomarker_candidate_ranking_tsv(report),
        )

    payload = {
        "biological_report_dir": (
            None if biological_report_dir is None else str(biological_report_dir)
        ),
        "ptm_report_dir": None if ptm_report_dir is None else str(ptm_report_dir),
        "selected_peptide_tsv": (
            None if selected_peptide_tsv is None else str(selected_peptide_tsv)
        ),
        "assay_interference_assay_tsv": (
            None
            if assay_interference_assay_tsv is None
            else str(assay_interference_assay_tsv)
        ),
        "summary": report.summary.to_dict(),
        "entries": [entry.to_dict() for entry in report.entries],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "candidate_tsv": (
                None if candidate_tsv_out is None else str(candidate_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_targeted_peptide_selection_command",
    "run_targeted_transition_selection_command",
    "run_targeted_assay_interference_command",
    "run_biomarker_candidate_ranking_command",
]
