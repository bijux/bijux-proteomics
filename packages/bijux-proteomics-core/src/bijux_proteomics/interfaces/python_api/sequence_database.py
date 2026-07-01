# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""FASTA provenance, decoy, and digestion Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
    hashlib,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    DecoyGenerationMode,
    DuplicateAccessionPolicy,
    FastaParseMode,
    PeptideDigestionMode,
    build_decoy_generation_manifest,
    build_decoy_generation_report,
    build_digest_manifest,
    build_fasta_provenance_manifest,
    build_theoretical_digest_bundle,
    digest_protein_records,
    export_peptide_protein_table_tsv,
    export_peptides_fasta,
    export_peptides_jsonl,
    export_peptides_parquet,
    export_peptides_tsv,
    generate_decoy_records,
    peptide_export_fingerprint,
    render_records_fasta,
    validate_target_decoy_database,
    write_theoretical_digest_bundle,
)
from bijux_proteomics.interfaces.support.sequence_support.digestion_parameters import (
    _resolve_cli_protease_rule,
    _resolve_cli_theoretical_digest_modifications,
)
from bijux_proteomics.interfaces.support.sequence_support.fasta_inputs import (
    _load_fasta_report,
)


def run_fasta_provenance_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    operation: str,
    out_path: Path,
) -> None:
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(duplicate_accession_policy),
        allow_rejected=True,
    )
    manifest = build_fasta_provenance_manifest(
        operation=operation,
        source_path=input_fasta,
        parse_mode=FastaParseMode(mode),
        input_record_count=report.total_records,
        accepted_record_count=len(report.accepted_records),
        rejected_record_count=len(report.rejected_records),
        output_record_count=len(report.accepted_records),
        parameters={
            "operation": operation,
            "duplicate_accession_policy": duplicate_accession_policy,
        },
    )
    _emit_json(manifest, out_path=out_path)


def run_fasta_decoy_command(
    input_fasta: Path,
    mode: str,
    decoy_mode: str,
    prefix: str,
    seed: int,
    decoys_only: bool,
    out_fasta: Path,
    report_out: Path | None,
    manifest_out: Path | None,
) -> None:
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    try:
        decoys = generate_decoy_records(
            report.accepted_records,
            mode=DecoyGenerationMode(decoy_mode),
            prefix=prefix,
            seed=seed,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    output_records = decoys if decoys_only else (*report.accepted_records, *decoys)
    out_fasta.write_text(render_records_fasta(tuple(output_records)))
    generation_report = build_decoy_generation_report(
        report.accepted_records,
        decoys,
        mode=DecoyGenerationMode(decoy_mode),
        prefix=prefix,
        seed=seed,
    )
    manifest = build_decoy_generation_manifest(
        input_records=report.accepted_records,
        output_records=tuple(output_records),
        mode=DecoyGenerationMode(decoy_mode),
        prefix=prefix,
        seed=seed,
        source_path=input_fasta,
    )
    if manifest_out is not None:
        manifest_out.write_text(manifest.to_stable_json() + "\n")
    validation = validate_target_decoy_database(tuple(output_records), prefix=prefix)
    payload = validation.to_dict()
    payload["reproducibility_hash"] = manifest.reproducibility_hash
    payload["output_sha256"] = manifest.output_sha256
    payload["generation_report"] = generation_report.to_dict()
    _emit_json(payload, out_path=report_out)


def run_target_decoy_validate_command(
    input_fasta: Path,
    mode: str,
    prefix: str,
    out_path: Path | None,
) -> None:
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    validation = validate_target_decoy_database(report.accepted_records, prefix=prefix)
    _emit_json(validation, out_path=out_path)


def run_digest_command(
    input_fasta: Path,
    mode: str,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    missed_cleavages: int,
    digestion_mode: str,
    min_length: int,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    export_format: str,
    out_path: Path,
    manifest_out: Path | None,
    peptide_protein_table_out: Path | None,
) -> None:
    try:
        protease_rule, custom_specification = _resolve_cli_protease_rule(
            protease=protease,
            custom_protease=custom_protease,
            custom_protease_name=custom_protease_name,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    peptides = digest_protein_records(
        report.accepted_records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        mode=PeptideDigestionMode(digestion_mode),
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )

    try:
        if export_format == "tsv":
            export_peptides_tsv(peptides, out_path)
        elif export_format == "jsonl":
            export_peptides_jsonl(peptides, out_path)
        elif export_format == "fasta":
            export_peptides_fasta(peptides, out_path)
        else:
            export_peptides_parquet(peptides, out_path)
        if peptide_protein_table_out is not None:
            export_peptide_protein_table_tsv(peptides, peptide_protein_table_out)
    except (RuntimeError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc

    manifest = build_digest_manifest(
        peptides=peptides,
        protease=protease_rule,
        digestion_mode=PeptideDigestionMode(digestion_mode),
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
        source_path=input_fasta,
        input_record_count=report.total_records,
    )
    if manifest_out is not None:
        manifest_out.write_text(manifest.to_stable_json() + "\n")

    payload = {
        "input_record_count": report.total_records,
        "output_peptide_count": len(peptides),
        "protease": protease_rule.name,
        "custom_protease": custom_specification,
        "digestion_mode": digestion_mode,
        "policy_hash": manifest.policy_hash,
        "export_format": export_format,
        "output_sha256": peptide_export_fingerprint(peptides),
        "output_path": str(out_path),
    }
    if peptide_protein_table_out is not None:
        payload["peptide_protein_table_path"] = str(peptide_protein_table_out)
        payload["peptide_protein_table_sha256"] = hashlib.sha256(
            peptide_protein_table_out.read_bytes()
        ).hexdigest()
    _emit_json(payload)


def run_theoretical_digest_command(
    input_fasta: Path,
    mode: str,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    missed_cleavages: int,
    digestion_mode: str,
    min_length: int,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    static_modifications: tuple[str, ...],
    variable_modifications: tuple[str, ...],
    registry_path: Path | None,
    allow_isotopic_labels: bool,
    allowed_label_families: tuple[str, ...],
    max_variants_per_peptide: int,
    out_dir: Path,
) -> None:
    try:
        protease_rule, custom_specification = _resolve_cli_protease_rule(
            protease=protease,
            custom_protease=custom_protease,
            custom_protease_name=custom_protease_name,
        )
        (
            registry,
            resolved_static,
            resolved_variable,
            labeling_policy,
        ) = _resolve_cli_theoretical_digest_modifications(
            static_modifications=static_modifications,
            variable_modifications=variable_modifications,
            registry_path=registry_path,
            allow_isotopic_labels=allow_isotopic_labels,
            allowed_label_families=allowed_label_families,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    bundle = build_theoretical_digest_bundle(
        report.accepted_records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        digestion_mode=PeptideDigestionMode(digestion_mode),
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
        static_modifications=resolved_static,
        variable_modifications=resolved_variable,
        registry=registry,
        labeling_policy=labeling_policy,
        max_variable_variants_per_peptide=max_variants_per_peptide,
    )

    try:
        peptides_path, mappings_path, summary_path = write_theoretical_digest_bundle(
            bundle,
            out_dir,
        )
    except OSError as exc:
        raise click.ClickException(str(exc)) from exc

    _emit_json(
        {
            "input_record_count": report.total_records,
            "protease": protease_rule.name,
            "custom_protease": custom_specification,
            "digestion_mode": digestion_mode,
            "static_modification_names": [
                definition.name for definition in resolved_static
            ],
            "variable_modification_names": [
                definition.name for definition in resolved_variable
            ],
            "search_space_hash": bundle.search_space_hash,
            "output_candidate_peptide_count": bundle.summary.output_candidate_peptide_count,
            "output_mapping_count": bundle.summary.output_mapping_count,
            "digest_peptides_path": str(peptides_path),
            "peptide_to_protein_path": str(mappings_path),
            "digest_summary_path": str(summary_path),
        }
    )


__all__ = [
    "run_fasta_provenance_command",
    "run_fasta_decoy_command",
    "run_target_decoy_validate_command",
    "run_digest_command",
    "run_theoretical_digest_command",
]
