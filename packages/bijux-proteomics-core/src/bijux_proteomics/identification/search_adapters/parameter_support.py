# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared parameter parsing helpers for search-adapter engines."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.search_adapters.contracts import (
    SearchModificationDefinition,
)

SUPPORTED_ENZYMES = {
    "trypsin",
    "trypsin/p",
    "lys-c",
    "lys-n",
    "arg-c",
    "asp-n",
    "glu-c",
    "chymotrypsin",
    "no_enzyme",
    "unspecific",
}


def parse_key_value_parameters(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        fields[key.strip()] = value.strip()
    return fields


def fixed_modifications_from_fields(
    fields: dict[str, str],
) -> tuple[SearchModificationDefinition, ...]:
    definitions: list[SearchModificationDefinition] = []
    for key, value in sorted(fields.items()):
        if not key.startswith("add_"):
            continue
        residue_tokens = key.split("_")
        if len(residue_tokens) < 2:
            continue
        site = residue_tokens[1][:1].upper()
        try:
            mass_delta = float(value)
        except ValueError:
            continue
        if mass_delta == 0.0:
            continue
        definitions.append(
            SearchModificationDefinition(
                site=site,
                mass_delta=mass_delta,
                variable=False,
                source_key=key,
            )
        )
    return tuple(definitions)


def variable_modifications_from_key_value_fields(
    fields: dict[str, str],
) -> tuple[SearchModificationDefinition, ...]:
    definitions: list[SearchModificationDefinition] = []
    for key, value in sorted(fields.items()):
        if not key.startswith("variable_mod"):
            continue
        tokens = value.split()
        if len(tokens) < 2:
            continue
        try:
            mass_delta = float(tokens[0])
        except ValueError:
            continue
        site = tokens[1].upper()
        definitions.append(
            SearchModificationDefinition(
                site=site,
                mass_delta=mass_delta,
                variable=True,
                source_key=key,
            )
        )
    return tuple(definitions)


def modification_definitions_from_compact_value(
    value: str | None,
    *,
    variable: bool,
    source_key: str,
) -> tuple[SearchModificationDefinition, ...]:
    if not value:
        return ()
    definitions: list[SearchModificationDefinition] = []
    for token in value.split(";"):
        entry = token.strip()
        if not entry or ":" not in entry:
            continue
        site, delta = entry.split(":", 1)
        site_clean = site.strip().upper()
        if not site_clean:
            continue
        try:
            mass_delta = float(delta.strip())
        except ValueError:
            continue
        definitions.append(
            SearchModificationDefinition(
                site=site_clean,
                mass_delta=mass_delta,
                variable=variable,
                source_key=f"{source_key}.{site_clean}",
            )
        )
    return tuple(definitions)
