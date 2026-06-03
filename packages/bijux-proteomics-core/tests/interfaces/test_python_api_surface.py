# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics.interfaces.python_api as python_api


def test_python_api_surface_exports_programmatic_command_entrypoints() -> None:
    assert hasattr(python_api, "run_program_template")
    assert hasattr(python_api, "run_fasta_parse_command")
    assert hasattr(python_api, "run_psm_inspect_command")
    assert hasattr(python_api, "run_compartment_biology_command")
    assert hasattr(python_api, "run_quantify_command")
    assert hasattr(python_api, "run_targeted_result_validator_command")
