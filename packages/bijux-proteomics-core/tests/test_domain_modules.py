# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.assays import AssayRequirement
from bijux_proteomics.constraints import ScientificConstraint
from bijux_proteomics.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.operating_model import OperatingModel
from bijux_proteomics.program_spec import ProgramSpec, ProgramStage
from bijux_proteomics.reviews import ReviewGate
from bijux_proteomics.targets import ProteinTarget


def test_domain_modules_define_program_components() -> None:
    target = ProteinTarget(
        target_id="target-1",
        name="Target 1",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize productive packing",
    )
    program = ProgramSpec(
        program_id="prog-1",
        name="binder rescue",
        objective="recover binding while preserving folding",
        stage=ProgramStage.DESIGN,
        target=target,
        constraints=[
            ScientificConstraint(
                constraint_id="surface-hydrophobics",
                category="developability",
                statement="avoid broad hydrophobic surface patches",
                rationale="reduce aggregation risk",
            )
        ],
        success_criteria=[
            SuccessCriterion(
                criterion_id="binding",
                metric="binding_score",
                direction=MeasurementDirection.MAXIMIZE,
                threshold=0.8,
            )
        ],
        assay_panel=[
            AssayRequirement(
                assay_id="primary-binding",
                purpose="confirm target engagement",
                readout="binding_score",
                sample_kind="biophysical",
                blocking=True,
            )
        ],
        review_gates=[
            ReviewGate(
                gate_id="pre-synthesis",
                name="Pre-synthesis review",
                required_roles=["scientist"],
                decision_inputs=["evidence_bundle"],
            )
        ],
        operating_model=OperatingModel(review_cadence="weekly"),
    )

    assert program.stage is ProgramStage.DESIGN
    assert program.assay_panel[0].blocking is True
    assert program.operating_model.review_cadence == "weekly"
