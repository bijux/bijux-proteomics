# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Generic search-table adapter manifest."""

from __future__ import annotations

from bijux_proteomics.identification.contracts import TargetDecoyLabelPolicy

from ..contracts import ScoreOrientation, SearchAdapterKind, SearchAdapterManifest


GENERIC_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.GENERIC,
    display_name="Generic search table",
    description="Normalize a user-mapped generic search-result table into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    native_columns=(),
    mapping=None,
    default_decoy_policy=TargetDecoyLabelPolicy(),
    supported_extensions=(".tsv", ".txt"),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_config_hash=True,
    supports_external_execution=False,
)

GENERIC_DIALECTS: tuple[()] = ()
