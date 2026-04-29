# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein digestion and peptide indexing contracts."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.chemistry import calculate_monoisotopic_peptide_mass
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class ProteaseCleavageMode(StrEnum):
    """Direction for protease cleavage semantics."""

    C_TERMINAL = "c_terminal"
    N_TERMINAL = "n_terminal"


class ProteaseRule(JsonModel):
    """Stable cleavage contract for one protease."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    cleavage_mode: ProteaseCleavageMode = ProteaseCleavageMode.C_TERMINAL
    cleavage_residues: str = Field(..., min_length=1)
    blocked_by_next: str = ""
    blocked_by_previous: str = ""
    description: str = ""

    @field_validator("cleavage_residues", "blocked_by_next", "blocked_by_previous")
    @classmethod
    def _normalize_residue_token(cls, value: str) -> str:
        return "".join(sorted(set(value.strip().upper())))


class PeptideDigestionMode(StrEnum):
    """Supported peptide digestion strategies."""

    FULL = "full"
    SEMI_SPECIFIC = "semi_specific"
    NON_SPECIFIC = "non_specific"


class DigestedPeptide(JsonModel):
    """One peptide generated from protein digestion."""

    model_config = ConfigDict(extra="forbid")

    source_accession: str = Field(..., min_length=1)
    source_identifier: str = Field(..., min_length=1)
    source_protein_family: str = Field(..., min_length=1)
    source_isoform: int | None = Field(default=None, ge=1)
    sequence: str = Field(..., min_length=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    missed_cleavages: int = Field(default=0, ge=0)
    protease: str = Field(..., min_length=1)
    digestion_mode: PeptideDigestionMode
    cleavage_type: Literal["enzymatic", "semi_specific", "non_specific"] = "enzymatic"

    @field_validator("sequence")
    @classmethod
    def _normalize_sequence(cls, value: str) -> str:
        return value.strip().upper()


class PeptideFilterReport(JsonModel):
    """Accounting for peptide-level post-digestion filtering."""

    model_config = ConfigDict(extra="forbid")

    input_peptides: int = Field(..., ge=0)
    output_peptides: int = Field(..., ge=0)
    excluded_by_length: int = Field(default=0, ge=0)
    excluded_by_mass: int = Field(default=0, ge=0)


class DigestDuplicateSequenceEntry(JsonModel):
    """One repeated peptide sequence with explicit occurrence accounting."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    occurrence_count: int = Field(..., ge=2)
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)


class DigestDuplicateAccounting(JsonModel):
    """Honest peptide duplicate accounting for one digestion result."""

    model_config = ConfigDict(extra="forbid")

    total_peptide_occurrences: int = Field(..., ge=0)
    unique_sequence_count: int = Field(..., ge=0)
    duplicate_sequence_count: int = Field(..., ge=0)
    duplicate_occurrence_count: int = Field(..., ge=0)
    repeated_sequences: tuple[DigestDuplicateSequenceEntry, ...] = Field(
        default_factory=tuple
    )


class PeptideUniqueness(StrEnum):
    """Classification of peptide uniqueness across proteins."""

    UNIQUE = "unique"
    SHARED_ISOFORM_FAMILY = "shared_isoform_family"
    SHARED = "shared"


class PeptideUniquenessEntry(JsonModel):
    """One peptide uniqueness classification entry."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    protein_families: tuple[str, ...] = Field(default_factory=tuple)
    uniqueness: PeptideUniqueness


class PeptideProteinIndexEntry(JsonModel):
    """Index entry from peptide sequence to source proteins and positions."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    protein_families: tuple[str, ...] = Field(default_factory=tuple)
    source_identifiers: tuple[str, ...] = Field(default_factory=tuple)
    coordinates: tuple["PeptideOriginCoordinate", ...] = Field(default_factory=tuple)
    uniqueness: PeptideUniqueness


class PeptideOriginCoordinate(JsonModel):
    """One peptide origin coordinate with preserved accession family metadata."""

    model_config = ConfigDict(extra="forbid")

    protein_accession: str = Field(..., min_length=1)
    protein_family: str = Field(..., min_length=1)
    source_identifier: str = Field(..., min_length=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    isoform: int | None = Field(default=None, ge=1)


class PeptideDigestManifest(JsonModel):
    """Stable manifest for one digestion job."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    digest_policy: "DigestPolicy"
    policy_hash: str = Field(..., min_length=64, max_length=64)
    protease: str = Field(..., min_length=1)
    digestion_mode: PeptideDigestionMode
    missed_cleavages: int = Field(..., ge=0)
    min_length: int | None = None
    max_length: int | None = None
    min_mass: float | None = None
    max_mass: float | None = None
    source_path: str | None = None
    source_sha256: str | None = None
    input_record_count: int = Field(..., ge=0)
    output_peptide_count: int = Field(..., ge=0)
    output_sha256: str = Field(..., min_length=64, max_length=64)


class DigestBenchmarkReport(JsonModel):
    """Measured digestion benchmark summary."""

    model_config = ConfigDict(extra="forbid")

    protein_count: int = Field(..., ge=0)
    total_residues: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    elapsed_seconds: float = Field(..., ge=0.0)
    peak_memory_bytes: int | None = Field(default=None, ge=0)
    peptides_per_second: float = Field(..., ge=0.0)


class DigestPolicy(JsonModel):
    """Stable digestion assumptions that must survive export and rerun."""

    model_config = ConfigDict(extra="forbid")

    protease: str = Field(..., min_length=1)
    cleavage_mode: ProteaseCleavageMode
    cleavage_residues: str = Field(..., min_length=1)
    blocked_by_next: str = ""
    blocked_by_previous: str = ""
    digestion_mode: PeptideDigestionMode
    missed_cleavages: int = Field(..., ge=0)
    min_length: int | None = None
    max_length: int | None = None
    min_mass: float | None = None
    max_mass: float | None = None


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


def parse_custom_protease_rule(
    specification: str, *, name: str = "custom"
) -> ProteaseRule:
    """Parse a user-defined protease rule from a compact textual form."""
    # Supported keys:
    # - ``after`` or ``before`` for cleavage residues
    # - ``block_next`` for residues that block a C-terminal cut
    # - ``block_previous`` for residues that block an N-terminal cut
    # - ``description`` for human-readable metadata

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


def filter_digested_peptides(
    peptides: tuple[DigestedPeptide, ...],
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    min_mass: float | None = None,
    max_mass: float | None = None,
) -> tuple[tuple[DigestedPeptide, ...], PeptideFilterReport]:
    """Filter digested peptides by sequence length."""
    filtered: list[DigestedPeptide] = []
    excluded_by_length = 0
    excluded_by_mass = 0
    for peptide in peptides:
        if min_length is not None and len(peptide.sequence) < min_length:
            excluded_by_length += 1
            continue
        if max_length is not None and len(peptide.sequence) > max_length:
            excluded_by_length += 1
            continue
        mass = _peptide_neutral_mass(peptide.sequence)
        if min_mass is not None and mass < min_mass:
            excluded_by_mass += 1
            continue
        if max_mass is not None and mass > max_mass:
            excluded_by_mass += 1
            continue
        filtered.append(peptide)
    return tuple(filtered), PeptideFilterReport(
        input_peptides=len(peptides),
        output_peptides=len(filtered),
        excluded_by_length=excluded_by_length,
        excluded_by_mass=excluded_by_mass,
    )


def classify_peptide_uniqueness(
    peptides: tuple[DigestedPeptide, ...],
) -> tuple[PeptideUniquenessEntry, ...]:
    """Classify peptides as unique or shared across parent proteins."""
    sequence_to_peptides: dict[str, list[DigestedPeptide]] = {}
    for peptide in peptides:
        sequence_to_peptides.setdefault(peptide.sequence, []).append(peptide)

    entries = [
        PeptideUniquenessEntry(
            sequence=sequence,
            protein_accessions=tuple(
                sorted({peptide.source_accession for peptide in members})
            ),
            protein_families=tuple(
                sorted({peptide.source_protein_family for peptide in members})
            ),
            uniqueness=_classify_peptide_uniqueness_members(members),
        )
        for sequence, members in sorted(sequence_to_peptides.items())
    ]
    return tuple(entries)


def build_digest_duplicate_accounting(
    peptides: tuple[DigestedPeptide, ...],
) -> DigestDuplicateAccounting:
    """Summarize repeated peptide sequences without hiding total occurrences."""
    grouped: dict[str, list[DigestedPeptide]] = {}
    for peptide in peptides:
        grouped.setdefault(peptide.sequence, []).append(peptide)

    repeated_sequences = tuple(
        DigestDuplicateSequenceEntry(
            sequence=sequence,
            occurrence_count=len(members),
            protein_accessions=tuple(
                sorted({member.source_accession for member in members})
            ),
        )
        for sequence, members in sorted(grouped.items())
        if len(members) > 1
    )
    return DigestDuplicateAccounting(
        total_peptide_occurrences=len(peptides),
        unique_sequence_count=len(grouped),
        duplicate_sequence_count=len(repeated_sequences),
        duplicate_occurrence_count=sum(
            entry.occurrence_count - 1 for entry in repeated_sequences
        ),
        repeated_sequences=repeated_sequences,
    )


def build_peptide_protein_index(
    peptides: tuple[DigestedPeptide, ...],
) -> tuple[PeptideProteinIndexEntry, ...]:
    """Build a stable peptide-to-protein index."""
    grouped: dict[str, list[DigestedPeptide]] = {}
    for peptide in peptides:
        grouped.setdefault(peptide.sequence, []).append(peptide)

    entries: list[PeptideProteinIndexEntry] = []
    for sequence, members in sorted(grouped.items()):
        accessions = tuple(sorted({member.source_accession for member in members}))
        protein_families = tuple(
            sorted({member.source_protein_family for member in members})
        )
        identifiers = tuple(sorted({member.source_identifier for member in members}))
        coordinate_keys = sorted(
            {
                (
                    member.source_accession,
                    member.source_protein_family,
                    member.source_identifier,
                    member.start,
                    member.end,
                    member.source_isoform,
                )
                for member in members
            }
        )
        coordinates = tuple(
            PeptideOriginCoordinate(
                protein_accession=accession,
                protein_family=protein_family,
                source_identifier=source_identifier,
                start=start,
                end=end,
                isoform=isoform,
            )
            for accession, protein_family, source_identifier, start, end, isoform in coordinate_keys
        )
        entries.append(
            PeptideProteinIndexEntry(
                sequence=sequence,
                protein_accessions=accessions,
                protein_families=protein_families,
                source_identifiers=identifiers,
                coordinates=coordinates,
                uniqueness=_classify_peptide_uniqueness_members(members),
            )
        )
    return tuple(entries)


def digest_protein_records(
    records: tuple[object, ...],
    *,
    protease: ProteaseRule | str = "trypsin",
    missed_cleavages: int = 0,
    mode: PeptideDigestionMode = PeptideDigestionMode.FULL,
    min_length: int = 1,
    max_length: int | None = None,
    min_mass: float | None = None,
    max_mass: float | None = None,
) -> tuple[DigestedPeptide, ...]:
    """Digest normalized protein records or FASTA-like records into peptides."""
    peptides: list[DigestedPeptide] = []
    for record in records:
        accession = getattr(record, "canonical_accession", None) or getattr(
            record, "identifier", None
        )
        identifier = getattr(record, "source_identifier", None) or getattr(
            record, "identifier", None
        )
        isoform = getattr(record, "isoform", None)
        residues = getattr(record, "residues", None)
        if accession is None or identifier is None or residues is None:
            raise TypeError(
                "digest_protein_records expects records with accession, identifier, and residues"
            )
        stable_accession = _stable_protein_accession(str(accession), isoform=isoform)
        peptides.extend(
            digest_sequence(
                residues,
                protease=protease,
                source_accession=stable_accession,
                source_identifier=str(identifier),
                source_protein_family=str(accession),
                source_isoform=isoform if isinstance(isoform, int) else None,
                missed_cleavages=missed_cleavages,
                mode=mode,
                min_length=min_length,
                max_length=max_length,
            )
        )
    filtered, _report = filter_digested_peptides(
        tuple(peptides),
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )
    return filtered


def digest_sequence(
    sequence: str,
    *,
    protease: ProteaseRule | str = "trypsin",
    source_accession: str = "sequence",
    source_identifier: str | None = None,
    source_protein_family: str | None = None,
    source_isoform: int | None = None,
    missed_cleavages: int = 0,
    mode: PeptideDigestionMode = PeptideDigestionMode.FULL,
    min_length: int = 1,
    max_length: int | None = None,
) -> tuple[DigestedPeptide, ...]:
    """Digest one sequence under the selected specificity mode."""
    normalized = sequence.strip().upper()
    rule = get_protease_rule(protease) if isinstance(protease, str) else protease
    boundaries = _full_digest_boundaries(normalized, rule)
    peptides: list[DigestedPeptide] = []
    identifier = source_identifier or source_accession
    protein_family = source_protein_family or source_accession
    max_peptide_length = max_length if max_length is not None else len(normalized)
    if mode is PeptideDigestionMode.NON_SPECIFIC:
        return _non_specific_digest(
            normalized,
            source_accession=source_accession,
            source_identifier=identifier,
            source_protein_family=protein_family,
            source_isoform=source_isoform,
            protease=rule.name,
            min_length=min_length,
            max_length=max_peptide_length,
        )
    if mode is PeptideDigestionMode.SEMI_SPECIFIC:
        return _semi_specific_digest(
            normalized,
            boundaries=boundaries,
            rule=rule,
            source_accession=source_accession,
            source_identifier=identifier,
            source_protein_family=protein_family,
            source_isoform=source_isoform,
            min_length=min_length,
            max_length=max_peptide_length,
        )
    for start_index, start in enumerate(boundaries[:-1]):
        max_span = min(missed_cleavages + 1, len(boundaries) - start_index - 1)
        for span in range(1, max_span + 1):
            end = boundaries[start_index + span]
            peptide = normalized[start:end]
            if (
                not peptide
                or len(peptide) < min_length
                or len(peptide) > max_peptide_length
            ):
                continue
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=identifier,
                    source_protein_family=protein_family,
                    source_isoform=source_isoform,
                    sequence=peptide,
                    start=start + 1,
                    end=end,
                    missed_cleavages=span - 1,
                    protease=rule.name,
                    digestion_mode=mode,
                    cleavage_type="enzymatic",
                )
            )
    return tuple(peptides)


def export_peptides_tsv(peptides: tuple[DigestedPeptide, ...], path: Path) -> Path:
    """Write a stable TSV export for digested peptides."""
    header = "\t".join(
        [
            "source_accession",
            "source_identifier",
            "sequence",
            "start",
            "end",
            "missed_cleavages",
            "protease",
            "digestion_mode",
            "cleavage_type",
            "neutral_mass",
        ]
    )
    lines = [header]
    for peptide in peptides:
        lines.append(
            "\t".join(
                [
                    peptide.source_accession,
                    peptide.source_identifier,
                    peptide.sequence,
                    str(peptide.start),
                    str(peptide.end),
                    str(peptide.missed_cleavages),
                    peptide.protease,
                    peptide.digestion_mode.value,
                    peptide.cleavage_type,
                    f"{_peptide_neutral_mass(peptide.sequence):.5f}",
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n")
    return path


def export_peptides_jsonl(peptides: tuple[DigestedPeptide, ...], path: Path) -> Path:
    """Write a stable JSONL export for digested peptides."""
    payload = []
    for peptide in peptides:
        entry = peptide.to_dict()
        entry["neutral_mass"] = round(_peptide_neutral_mass(peptide.sequence), 5)
        payload.append(entry)
    path.write_text(
        "\n".join(json.dumps(entry, sort_keys=True) for entry in payload) + "\n"
    )
    return path


def export_peptides_parquet(peptides: tuple[DigestedPeptide, ...], path: Path) -> Path:
    """Write an optional Parquet export for digested peptides."""
    try:
        import pyarrow as pa  # type: ignore[import-not-found]
        import pyarrow.parquet as pq  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Parquet export requires optional dependency 'pyarrow'"
        ) from exc

    rows = []
    for peptide in peptides:
        rows.append(
            {
                "source_accession": peptide.source_accession,
                "source_identifier": peptide.source_identifier,
                "sequence": peptide.sequence,
                "start": peptide.start,
                "end": peptide.end,
                "missed_cleavages": peptide.missed_cleavages,
                "protease": peptide.protease,
                "digestion_mode": peptide.digestion_mode.value,
                "cleavage_type": peptide.cleavage_type,
                "neutral_mass": round(_peptide_neutral_mass(peptide.sequence), 5),
            }
        )
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)
    return path


def peptide_export_fingerprint(peptides: tuple[DigestedPeptide, ...]) -> str:
    """Return a stable digest over peptide export content."""
    payload = [
        {
            "source_accession": peptide.source_accession,
            "source_identifier": peptide.source_identifier,
            "sequence": peptide.sequence,
            "start": peptide.start,
            "end": peptide.end,
            "missed_cleavages": peptide.missed_cleavages,
            "protease": peptide.protease,
            "digestion_mode": peptide.digestion_mode.value,
            "cleavage_type": peptide.cleavage_type,
            "neutral_mass": round(_peptide_neutral_mass(peptide.sequence), 5),
        }
        for peptide in peptides
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def build_digest_policy(
    *,
    protease: ProteaseRule | str,
    digestion_mode: PeptideDigestionMode,
    missed_cleavages: int,
    min_length: int | None,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
) -> DigestPolicy:
    """Build the stable digestion policy contract for one run."""
    rule = get_protease_rule(protease) if isinstance(protease, str) else protease
    return DigestPolicy(
        protease=rule.name,
        cleavage_mode=rule.cleavage_mode,
        cleavage_residues=rule.cleavage_residues,
        blocked_by_next=rule.blocked_by_next,
        blocked_by_previous=rule.blocked_by_previous,
        digestion_mode=digestion_mode,
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )


def compute_digest_policy_hash(policy: DigestPolicy) -> str:
    """Return a stable hash over digestion assumptions."""
    return hashlib.sha256(
        json.dumps(policy.to_dict(), sort_keys=True).encode("utf-8")
    ).hexdigest()


def build_digest_manifest(
    *,
    peptides: tuple[DigestedPeptide, ...],
    protease: str,
    digestion_mode: PeptideDigestionMode,
    missed_cleavages: int,
    min_length: int | None,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    source_path: Path | None,
    input_record_count: int,
) -> PeptideDigestManifest:
    """Build a stable digestion manifest."""
    digest_policy = build_digest_policy(
        protease=protease,
        digestion_mode=digestion_mode,
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )
    source_sha256 = (
        hashlib.sha256(source_path.read_bytes()).hexdigest()
        if source_path is not None
        else None
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="peptide_digest_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = PeptideDigestManifest(
        document_schema=schema,
        digest_policy=digest_policy,
        policy_hash=compute_digest_policy_hash(digest_policy),
        protease=protease,
        digestion_mode=digestion_mode,
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
        source_path=str(source_path) if source_path is not None else None,
        source_sha256=source_sha256,
        input_record_count=input_record_count,
        output_peptide_count=len(peptides),
        output_sha256=peptide_export_fingerprint(peptides),
    )
    payload = manifest.to_dict()
    return manifest.model_copy(
        update={"document_schema": manifest.document_schema.with_content_hash(payload)}
    )


def build_digest_benchmark_report(
    *,
    protein_count: int,
    total_residues: int,
    peptides: tuple[DigestedPeptide, ...],
    elapsed_seconds: float,
    peak_memory_bytes: int | None = None,
) -> DigestBenchmarkReport:
    """Build an explicit digestion benchmark report."""
    return DigestBenchmarkReport(
        protein_count=protein_count,
        total_residues=total_residues,
        peptide_count=len(peptides),
        elapsed_seconds=elapsed_seconds,
        peak_memory_bytes=peak_memory_bytes,
        peptides_per_second=(
            len(peptides) / elapsed_seconds if elapsed_seconds > 0 else 0.0
        ),
    )


def _classify_peptide_uniqueness_members(
    peptides: list[DigestedPeptide] | tuple[DigestedPeptide, ...],
) -> PeptideUniqueness:
    accessions = {peptide.source_accession for peptide in peptides}
    if len(accessions) == 1:
        return PeptideUniqueness.UNIQUE
    protein_families = {peptide.source_protein_family for peptide in peptides}
    if len(protein_families) == 1:
        return PeptideUniqueness.SHARED_ISOFORM_FAMILY
    return PeptideUniqueness.SHARED


def _full_digest_boundaries(sequence: str, rule: ProteaseRule) -> tuple[int, ...]:
    boundaries = [0]
    if not sequence:
        return (0,)

    if rule.cleavage_mode is ProteaseCleavageMode.C_TERMINAL:
        for index, residue in enumerate(sequence):
            if residue not in rule.cleavage_residues:
                continue
            next_residue = sequence[index + 1] if index + 1 < len(sequence) else None
            if next_residue is not None and next_residue in rule.blocked_by_next:
                continue
            boundaries.append(index + 1)
    else:
        for index, residue in enumerate(sequence):
            if residue not in rule.cleavage_residues:
                continue
            previous_residue = sequence[index - 1] if index > 0 else None
            if (
                previous_residue is not None
                and previous_residue in rule.blocked_by_previous
            ):
                continue
            if index not in boundaries:
                boundaries.append(index)

    if boundaries[-1] != len(sequence):
        boundaries.append(len(sequence))
    return tuple(boundaries)


def _semi_specific_digest(
    sequence: str,
    *,
    boundaries: tuple[int, ...],
    rule: ProteaseRule,
    source_accession: str,
    source_identifier: str,
    source_protein_family: str,
    source_isoform: int | None,
    min_length: int,
    max_length: int,
) -> tuple[DigestedPeptide, ...]:
    peptides: list[DigestedPeptide] = []
    seen: set[tuple[int, int]] = set()
    enzymatic_bounds = set(boundaries)

    for start in boundaries[:-1]:
        for end in range(start + 1, len(sequence) + 1):
            cleavage_type: Literal["enzymatic", "semi_specific", "non_specific"]
            if end not in enzymatic_bounds:
                cleavage_type = "semi_specific"
            else:
                cleavage_type = "enzymatic"
            bounds = (start, end)
            if bounds in seen:
                continue
            length = end - start
            if length < min_length or length > max_length:
                continue
            seen.add(bounds)
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=source_identifier,
                    source_protein_family=source_protein_family,
                    source_isoform=source_isoform,
                    sequence=sequence[start:end],
                    start=start + 1,
                    end=end,
                    missed_cleavages=0,
                    protease=rule.name,
                    digestion_mode=PeptideDigestionMode.SEMI_SPECIFIC,
                    cleavage_type=cleavage_type,
                )
            )

    for start in range(len(sequence)):
        if start in enzymatic_bounds:
            continue
        for end in boundaries[1:]:
            if end <= start:
                continue
            bounds = (start, end)
            if bounds in seen:
                continue
            length = end - start
            if length < min_length or length > max_length:
                continue
            seen.add(bounds)
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=source_identifier,
                    source_protein_family=source_protein_family,
                    source_isoform=source_isoform,
                    sequence=sequence[start:end],
                    start=start + 1,
                    end=end,
                    missed_cleavages=0,
                    protease=rule.name,
                    digestion_mode=PeptideDigestionMode.SEMI_SPECIFIC,
                    cleavage_type="semi_specific",
                )
            )

    peptides.sort(key=lambda peptide: (peptide.start, peptide.end, peptide.sequence))
    return tuple(peptides)


def _non_specific_digest(
    sequence: str,
    *,
    source_accession: str,
    source_identifier: str,
    source_protein_family: str,
    source_isoform: int | None,
    protease: str,
    min_length: int,
    max_length: int,
) -> tuple[DigestedPeptide, ...]:
    peptides: list[DigestedPeptide] = []
    for start in range(len(sequence)):
        for end in range(
            start + min_length, min(len(sequence), start + max_length) + 1
        ):
            peptide = sequence[start:end]
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=source_identifier,
                    source_protein_family=source_protein_family,
                    source_isoform=source_isoform,
                    sequence=peptide,
                    start=start + 1,
                    end=end,
                    missed_cleavages=0,
                    protease=protease,
                    digestion_mode=PeptideDigestionMode.NON_SPECIFIC,
                    cleavage_type="non_specific",
                )
            )
    return tuple(peptides)


def _peptide_neutral_mass(sequence: str) -> float:
    return calculate_monoisotopic_peptide_mass(sequence)


def _stable_protein_accession(accession: str, *, isoform: int | None) -> str:
    if isoform is None:
        return accession
    return f"{accession}-{isoform}"
