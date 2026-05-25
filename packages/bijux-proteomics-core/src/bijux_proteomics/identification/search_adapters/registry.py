# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Registry assembly for built-in search adapters and dialects."""

from __future__ import annotations

from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterCapability,
    SearchAdapterDialectManifest,
    SearchAdapterKind,
    SearchAdapterManifest,
)
from bijux_proteomics.identification.search_adapters.engines.comet import COMET_DIALECTS, COMET_MANIFEST
from bijux_proteomics.identification.search_adapters.engines.diann import DIANN_DIALECTS, DIANN_MANIFEST
from bijux_proteomics.identification.search_adapters.engines.generic import GENERIC_MANIFEST
from bijux_proteomics.identification.search_adapters.engines.maxquant import MAXQUANT_DIALECTS, MAXQUANT_MANIFEST
from bijux_proteomics.identification.search_adapters.engines.msfragger import MSFRAGGER_DIALECTS, MSFRAGGER_MANIFEST
from bijux_proteomics.identification.search_adapters.engines.sage import SAGE_DIALECTS, SAGE_MANIFEST
from bijux_proteomics.identification.search_adapters.engines.spectronaut import SPECTRONAUT_DIALECTS, SPECTRONAUT_MANIFEST


def _default_dialect_from_manifest(
    manifest: SearchAdapterManifest,
) -> SearchAdapterDialectManifest | None:
    if manifest.mapping is None:
        return None
    return SearchAdapterDialectManifest(
        adapter_kind=manifest.adapter_kind,
        dialect_id="default",
        display_name=manifest.display_name,
        description=manifest.description,
        score_family=manifest.score_family,
        result_family=manifest.result_family,
        native_columns=manifest.native_columns,
        mapping=manifest.mapping,
    )


def search_adapter_registry() -> dict[SearchAdapterKind, SearchAdapterManifest]:
    """Return the built-in search adapter registry."""
    manifests = (
        COMET_MANIFEST,
        MSFRAGGER_MANIFEST,
        SAGE_MANIFEST,
        MAXQUANT_MANIFEST,
        DIANN_MANIFEST,
        SPECTRONAUT_MANIFEST,
        GENERIC_MANIFEST,
    )
    return {manifest.adapter_kind: manifest for manifest in manifests}


def search_adapter_dialect_registry() -> dict[
    tuple[SearchAdapterKind, str], SearchAdapterDialectManifest
]:
    """Return the built-in search adapter dialect registry."""
    dialects = [
        dialect
        for dialect in (
            _default_dialect_from_manifest(manifest)
            for manifest in search_adapter_registry().values()
        )
        if dialect is not None
    ]
    dialects.extend([*COMET_DIALECTS, *MSFRAGGER_DIALECTS, *SAGE_DIALECTS, *MAXQUANT_DIALECTS, *DIANN_DIALECTS, *SPECTRONAUT_DIALECTS])
    return {(dialect.adapter_kind, dialect.dialect_id): dialect for dialect in dialects}


def get_search_adapter_manifest(adapter_kind: SearchAdapterKind) -> SearchAdapterManifest:
    """Fetch one built-in adapter manifest."""
    return search_adapter_registry()[adapter_kind]


def resolve_search_adapter_dialect(*, adapter_kind: SearchAdapterKind, dialect_id: str, additional_dialects: tuple[SearchAdapterDialectManifest, ...]) -> SearchAdapterDialectManifest | None:
    built_in = search_adapter_dialect_registry()
    extensions = {(dialect.adapter_kind, dialect.dialect_id): dialect for dialect in additional_dialects}
    if len(extensions) != len(additional_dialects):
        raise ValueError("additional adapter dialects must not contain duplicates")
    key = (adapter_kind, dialect_id)
    dialect = extensions.get(key) or built_in.get(key)
    if dialect is None:
        if adapter_kind is SearchAdapterKind.GENERIC and dialect_id == "default":
            return None
        raise ValueError(f"search adapter dialect {dialect_id!r} is not registered for {adapter_kind.value!r}")
    return dialect


def manifest_for_dialect(*, adapter_kind: SearchAdapterKind, dialect: SearchAdapterDialectManifest | None) -> SearchAdapterManifest:
    manifest = get_search_adapter_manifest(adapter_kind)
    if dialect is None:
        return manifest
    return manifest.model_copy(update={
        "description": dialect.description,
        "display_name": dialect.display_name,
        "score_orientation": dialect.score_orientation or manifest.score_orientation,
        "score_family": dialect.score_family,
        "result_family": dialect.result_family,
        "native_columns": dialect.native_columns,
        "mapping": dialect.mapping,
    })


def build_search_adapter_capability_matrix() -> tuple[SearchAdapterCapability, ...]:
    """Build a stable capability matrix over built-in search adapters."""
    rows = [
        SearchAdapterCapability(
            adapter_kind=manifest.adapter_kind,
            display_name=manifest.display_name,
            score_orientation=manifest.score_orientation,
            score_family=manifest.score_family,
            result_family=manifest.result_family,
            supports_q_value=manifest.supports_q_value,
            supports_explicit_decoy_label=manifest.supports_explicit_decoy_label,
            supports_protein_refs=manifest.supports_protein_refs,
            supports_config_hash=manifest.supports_config_hash,
            supports_external_execution=manifest.supports_external_execution,
            native_columns=manifest.native_columns,
        )
        for manifest in search_adapter_registry().values()
    ]
    return tuple(sorted(rows, key=lambda row: row.adapter_kind.value))
