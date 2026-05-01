# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.external_exec_iteration13 import (
    SlurmJobScriptInput,
    export_slurm_job_script,
)


def test_export_slurm_job_script_includes_resources_env_and_artifact_path() -> None:
    script = export_slurm_job_script(
        SlurmJobScriptInput(
            job_name="proteomics-qc",
            time_limit="02:00:00",
            cpus=8,
            memory_gb=32,
            scratch_dir="/scratch/job123",
            log_path="artifacts/slurm.log",
            environment_exports={"OMP_NUM_THREADS": "8"},
            artifact_dir="artifacts/run123",
            command="python3 -m bijux_proteomics.cli run",
        )
    )

    assert "#SBATCH --cpus-per-task=8" in script.script_text
    assert "export OMP_NUM_THREADS=8" in script.script_text
    assert "mkdir -p artifacts/run123" in script.script_text
