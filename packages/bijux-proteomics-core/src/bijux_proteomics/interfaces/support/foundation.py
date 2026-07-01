# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Shared standard imports and lightweight domain entrypoints for CLI modules."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import time
from typing import Any

import click

from bijux_proteomics.chemistry.fragments import (
    FragmentIonSeries,
    build_fragment_ion_review_report,
    calculate_fragment_ions,
    render_fragment_ion_report_tsv,
)
from bijux_proteomics.chemistry.isotopes import (
    IsotopicLabelingPolicy,
    approximate_peptide_isotope_envelope,
    build_peptide_elemental_composition,
    predict_peptide_isotope_envelopes,
    render_isotope_envelopes_tsv,
)
from bijux_proteomics.chemistry.mass import build_peptide_charge_state
from bijux_proteomics.chemistry.modifications import (
    ModificationRegistryDocument,
    SearchEngineModifiedPeptideDialect,
    StaticModification,
    VariableModification,
    build_modification_localization_advisory,
    build_modification_resolution_report,
    build_modified_peptide,
    build_search_engine_modified_peptide_report,
    canonicalize_modified_peptide,
    get_modification,
    load_modification_registry,
)
from bijux_proteomics.domain.errors import (
    ProteomicsOperatorError,
    ProteomicsOperatorErrorCode,
)
from bijux_proteomics.domain.program_spec import (
    ProgramSpec,
    create_program_spec,
    program_summary,
)

__all__ = [
    "Any",
    "FragmentIonSeries",
    "IsotopicLabelingPolicy",
    "ModificationRegistryDocument",
    "Path",
    "ProgramSpec",
    "ProteomicsOperatorError",
    "ProteomicsOperatorErrorCode",
    "SearchEngineModifiedPeptideDialect",
    "StaticModification",
    "VariableModification",
    "approximate_peptide_isotope_envelope",
    "build_fragment_ion_review_report",
    "build_modification_localization_advisory",
    "build_modification_resolution_report",
    "build_modified_peptide",
    "build_peptide_charge_state",
    "build_peptide_elemental_composition",
    "build_search_engine_modified_peptide_report",
    "calculate_fragment_ions",
    "canonicalize_modified_peptide",
    "click",
    "create_program_spec",
    "csv",
    "get_modification",
    "hashlib",
    "json",
    "load_modification_registry",
    "predict_peptide_isotope_envelopes",
    "program_summary",
    "render_fragment_ion_report_tsv",
    "render_isotope_envelopes_tsv",
    "time",
]
