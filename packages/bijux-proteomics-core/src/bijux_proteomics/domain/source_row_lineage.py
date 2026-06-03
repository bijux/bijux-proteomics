# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical source-row lineage for final scientific outputs."""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics_foundation import JsonModel


class SourceRowLineage(JsonModel):
    """Stable row-level audit lineage for one final output row."""

    model_config = ConfigDict(extra="forbid")

    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    derived_no_source_reason: str | None = None

    @field_validator("source_row_refs", mode="before")
    @classmethod
    def _normalize_source_row_refs(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        tokens: tuple[str, ...]
        if isinstance(value, str):
            tokens = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("source_row_refs must be iterable")
            tokens = tuple(str(token) for token in value)
        normalized: list[str] = []
        for token in tokens:
            text = token.strip()
            if not text:
                continue
            input_file, separator, row_number = text.rpartition(":")
            if not separator or not input_file.strip() or not row_number.strip():
                raise ValueError(
                    "source_row_refs must use the stable '<input_file>:<row_number>' form"
                )
            normalized.append(f"{input_file.strip()}:{row_number.strip()}")
        return tuple(dict.fromkeys(normalized))

    @field_validator("derived_no_source_reason", mode="before")
    @classmethod
    def _normalize_derived_no_source_reason(cls, value: object) -> str | None:
        if value in (None, ""):
            return None
        text = str(value).strip()
        if not text:
            return None
        return text

    @model_validator(mode="after")
    def _require_row_refs_or_reason(self) -> SourceRowLineage:
        if self.source_row_refs and self.derived_no_source_reason is not None:
            raise ValueError(
                "source-row lineage must carry concrete refs or one derived-no-source reason, not both"
            )
        if not self.source_row_refs and self.derived_no_source_reason is None:
            raise ValueError(
                "source-row lineage requires concrete refs or an explicit derived-no-source reason"
            )
        return self

    @classmethod
    def from_source_row_refs(
        cls,
        source_row_refs: Iterable[str],
    ) -> SourceRowLineage:
        """Create one lineage object from exact source-row references."""

        return cls(source_row_refs=tuple(source_row_refs))

    @classmethod
    def from_derived_reason(
        cls,
        reason: str,
    ) -> SourceRowLineage:
        """Create one lineage object for a governed derived surface without direct rows."""

        return cls(derived_no_source_reason=reason)

    @classmethod
    def from_imported_provenances(
        cls,
        provenances: Iterable[ImportedEvidenceProvenance],
        *,
        derived_no_source_reason: str | None = None,
    ) -> SourceRowLineage:
        """Create exact source-row lineage from imported provenance records."""

        source_row_refs: list[str] = []
        for provenance in provenances:
            source_row_refs.extend(_source_row_refs_from_imported_provenance(provenance))
        if source_row_refs:
            return cls.from_source_row_refs(source_row_refs)
        if derived_no_source_reason is None:
            raise ValueError(
                "imported provenance did not preserve exact file-row pairs; provide a derived_no_source_reason"
            )
        return cls.from_derived_reason(derived_no_source_reason)

    @property
    def source_row_chain(self) -> str:
        """Render one stable TSV cell for concrete source-row lineage."""

        return ";".join(self.source_row_refs)


def _source_row_refs_from_imported_provenance(
    provenance: ImportedEvidenceProvenance,
) -> tuple[str, ...]:
    if not provenance.source_files or not provenance.source_row_numbers:
        return ()
    if len(provenance.source_files) == 1:
        source_file = provenance.source_files[0]
        return tuple(
            f"{source_file}:{row_number}"
            for row_number in provenance.source_row_numbers
        )
    if len(provenance.source_row_numbers) == 1:
        row_number = provenance.source_row_numbers[0]
        return tuple(
            f"{source_file}:{row_number}"
            for source_file in provenance.source_files
        )
    raise ValueError(
        "imported provenance must preserve one exact file-row pairing or one file with multiple row numbers"
    )


__all__ = ["SourceRowLineage"]
