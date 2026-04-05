# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Local RoseTTAFold provider."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess  # nosec B404, noqa: S603
import tempfile
import time

from loguru import logger

from agentic_proteins.providers.base import (
    BaseProvider,
    PredictionResult,
    ProviderMetadata,
    _time_left,
)
from agentic_proteins.providers.errors import PredictionError


class LocalRoseTTAFoldProvider(BaseProvider):
    """Local RoseTTAFold provider."""

    name = "local_rosettafold"
    metadata = ProviderMetadata(name=name, experimental=False)

    def __init__(
        self,
        executable: str = "rf_allatom_predict.py",
        docker: bool = True,
        weights_path: str = "models/rosettafold/RFAA_paper_weights.pt",
    ) -> None:
        """Initializes the LocalRoseTTAFoldProvider.

        Args:
            executable: The executable path.
            docker: Whether to use Docker.
            weights_path: Path to weights.
        """
        self.executable = executable
        self.docker = docker
        self.weights_path = weights_path
        self.docker_image = os.getenv(
            "ROSETTA_DOCKER_IMAGE", "ghcr.io/rosetta/protein-design@sha256:deadbeef"
        )  # Pin digest
        if docker and shutil.which("docker") is None:
            raise ValueError("Docker required for RoseTTAFold but not installed")
        if not os.path.exists(self.weights_path):
            logger.warning(
                f"RoseTTAFold weights not found at {self.weights_path}; ensure downloaded."
            )

    def healthcheck(self) -> bool:
        """Checks the health of the provider.

        Returns:
            True if healthy, False otherwise.
        """
        if self.docker:
            try:
                docker_bin = shutil.which("docker")
                if not docker_bin:
                    return False

                subprocess.run(  # noqa: S603  # nosec B603
                    [docker_bin, "image", "inspect", self.docker_image],  # type: ignore[list-item]
                    capture_output=True,
                    check=True,
                    timeout=5,
                )
                # Check GPU visibility
                subprocess.run(  # noqa: S603  # nosec B603
                    [
                        docker_bin,  # type: ignore[list-item]
                        "run",
                        "--rm",
                        "--gpus",
                        "all",
                        self.docker_image,
                        "nvidia-smi",
                        "--query-gpu=index",
                        "--format=csv",
                    ],
                    capture_output=True,
                    check=True,
                    timeout=5,
                )
                # Check writable /workspace
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_cmd = [
                        docker_bin,  # type: ignore[list-item]
                        "run",
                        "--rm",
                        "-v",
                        f"{temp_dir}:/workspace",
                        self.docker_image,
                        "touch",
                        "/workspace/test.txt",
                    ]
                    subprocess.run(  # noqa: S603  # nosec B603
                        test_cmd, capture_output=True, check=True, timeout=5
                    )
                return os.access(self.weights_path, os.R_OK)
            except Exception:
                return False
        else:
            return os.path.exists(self.executable) and os.access(
                self.weights_path, os.R_OK
            )

    def predict(
        self, sequence: str, timeout: float = 600.0, seed: int | None = None
    ) -> PredictionResult:
        """Predicts the protein structure.

        Args:
            sequence: The amino acid sequence.
            timeout: The timeout in seconds.
            seed: The random seed.

        Returns:
            The prediction result.

        Raises:
            PredictionError: On failure.
        """
        start_time = time.time()
        deadline = start_time + timeout
        if len(sequence) == 0:
            raise PredictionError("Empty sequence", code="BAD_INPUT")
        max_len = int(os.getenv("ROSETTAFOLD_MAX_LEN", "1200"))
        if len(sequence) > max_len:
            raise PredictionError(
                f"Sequence too long for RoseTTAFold (max: {max_len})", code="BAD_INPUT"
            )
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                if _time_left(deadline) <= 0:
                    raise PredictionError("Timeout before setup", code="TIMEOUT")
                fasta_path = os.path.join(temp_dir, "input.fasta")
                with open(fasta_path, "w") as f:
                    f.write(f">seq\n{sequence}\n")
                output_dir = os.path.join(temp_dir, "output")
                os.mkdir(output_dir)
                if self.docker:
                    script_name = Path(self.executable).name
                    if Path(self.executable).exists():
                        shutil.copy2(self.executable, Path(temp_dir) / script_name)
                    in_fa = "/workspace/input.fasta"
                    out_dir = "/workspace/output"
                    weights_in = f"/models/{os.path.basename(self.weights_path)}"
                    cmd = [
                        "docker",
                        "run",
                        "--rm",
                        "--network=none",  # Safer
                        "--gpus",
                        "all",
                        "-w",
                        "/workspace",
                        "-v",
                        f"{temp_dir}:/workspace",
                        "-v",
                        f"{os.path.dirname(self.weights_path)}:/models:ro",
                        "-e",
                        f"DB_UR30={os.getenv('DB_UR30', '')}",
                        self.docker_image,
                        "python",
                        f"/workspace/{script_name}",
                        "--fasta",
                        in_fa,
                        "--out_dir",
                        out_dir,
                        "--weights",
                        weights_in,
                    ]
                else:
                    cmd = [
                        "python",
                        self.executable,
                        "--fasta",
                        fasta_path,
                        "--out_dir",
                        output_dir,
                        "--weights",
                        self.weights_path,
                    ]
                if _time_left(deadline) <= 0:
                    raise PredictionError("Timeout before subprocess", code="TIMEOUT")
                try:
                    result = subprocess.run(  # noqa: S603  # nosec B603
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=_time_left(deadline),
                        cwd=None if self.docker else temp_dir,
                        shell=False,
                    )
                except subprocess.TimeoutExpired as te:
                    raise PredictionError(
                        "RoseTTAFold run timed out", code="TIMEOUT"
                    ) from te
                if result.returncode != 0:
                    err_tail = f"Exit: {result.returncode}, stderr: {result.stderr[-500:] if result.stderr else ''}"
                    raise PredictionError(
                        f"RoseTTAFold failed: {err_tail}", code="REMOTE_ERROR"
                    )
                pdb_files = list(Path(output_dir).glob("*.pdb"))
                if not pdb_files:
                    raise PredictionError(
                        "No PDB output from RoseTTAFold", code="NO_OUTPUT"
                    )
                pdb_path = pdb_files[0]
                with open(pdb_path) as f:
                    pdb_text = f.read()
                out_tail = result.stdout[-500:] if result.stdout else ""
                raw_data = {
                    "cmd_output": out_tail,
                    "stderr_tail": result.stderr[-500:] if result.stderr else "",
                    "latency": time.time() - start_time,
                    "exit_code": result.returncode,
                    "seed": seed,
                }
                return PredictionResult(pdb_text, self.name, raw_data)
            finally:
                pass
