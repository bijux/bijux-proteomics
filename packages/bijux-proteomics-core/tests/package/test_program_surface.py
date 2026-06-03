# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib

from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.program_spec import ProgramSpec, ProgramStage
from bijux_proteomics.domain.targets import OutcomeSeverity, TargetOutcome
from bijux_proteomics.programs import build_program_brief, create_program_spec


def test_package_program_surface_exports_program_contract_types() -> None:
    module = importlib.import_module("bijux_proteomics.programs")

    assert module.ProgramSpec is ProgramSpec
    assert module.MeasurementDirection is MeasurementDirection
    assert module.build_program_brief is build_program_brief


def test_build_program_brief_summarizes_metrics_and_blockers() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="repair import contracts",
        objective="stabilize program surface",
        target_id="tgt-1",
        target_name="Import Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize package boundary semantics",
    ).model_copy(
        update={
            "stage": ProgramStage.REVIEW,
            "success_criteria": [
                SuccessCriterion(
                    criterion_id="binding",
                    metric="binding_score",
                    direction=MeasurementDirection.MAXIMIZE,
                    threshold=0.8,
                ),
                SuccessCriterion(
                    criterion_id="liability",
                    metric="aggregation_risk",
                    direction=MeasurementDirection.MINIMIZE,
                    threshold=0.2,
                ),
            ],
            "target": create_program_spec(
                program_id="prog-target",
                name="target program",
                objective="target only",
                target_id="tgt-1",
                target_name="Import Target",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                organism="human",
                mechanism="target mechanism",
            ).target.model_copy(
                update={
                    "blocked_outcome_records": [
                        TargetOutcome(
                            code="stale-runtime-import",
                            summary="stale runtime import edge",
                            severity=OutcomeSeverity.HIGH,
                        )
                    ]
                }
            ),
        }
    )

    brief = build_program_brief(program)

    assert brief.program_id == "prog-1"
    assert brief.measurement_metrics == ("binding_score", "aggregation_risk")
    assert brief.maximize_metrics == ("binding_score",)
    assert brief.minimize_metrics == ("aggregation_risk",)
    assert brief.blocked_outcome_codes == ("stale-runtime-import",)
