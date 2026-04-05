# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Local ESMFold provider."""

from __future__ import annotations

import os
import threading
import time
from typing import Any

from Bio.SeqUtils import seq3
from loguru import logger
import torch

from agentic_proteins.providers.base import (
    BaseProvider,
    PredictionResult,
    ProviderMetadata,
    _time_left,
)
from agentic_proteins.providers.errors import PredictionError


class LocalESMFoldProvider(BaseProvider):
    """Local ESMFold provider."""

    name = "local_esmfold"
    metadata = ProviderMetadata(name=name, experimental=False)

    def __init__(
        self, model_path: str = "models/esmfold", token: str | None = None
    ) -> None:
        """Initializes the LocalESMFoldProvider.

        Args:
            model_path: Path to the model.
            token: Hugging Face token.
        """
        self.revision = None
        self.model_path = model_path
        self.token = (token or os.getenv("HF_TOKEN") or "").strip()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer: Any = None
        self.model: Any = None
        self._model_loaded = False
        self._fail_count = 0
        self._circuit_open = False
        self._opened_at = 0.0
        self._lock = threading.RLock()
        self._infer_lock = threading.RLock()
        self.MAX_FAILS = 3
        self.COOLDOWN = 60.0

    def _load_model(self) -> None:
        """Loads the ESMFold model."""
        with self._lock:
            if self._model_loaded:
                return
            try:
                from transformers import (
                    EsmForProteinFolding,
                    EsmTokenizer,
                )

                # Check if local path exists; fallback to remote repo
                load_from = (
                    self.model_path
                    if os.path.exists(self.model_path)
                    else "facebook/esmfold_v1"
                )
                dtype = torch.float16 if self.device == "cuda" else torch.float32
                hf_revision = (
                    self.revision
                    or os.getenv("ESMFOLD_REVISION")
                    or "c231ea555c5fd3b4d91b0760351599c726541754"  # Pinned commit SHA for security
                )
                self.tokenizer = EsmTokenizer.from_pretrained(  # nosec B615
                    load_from,
                    revision=hf_revision,
                    token=self.token or None,
                )
                self.model = EsmForProteinFolding.from_pretrained(  # nosec B615
                    load_from,
                    revision=hf_revision,
                    torch_dtype=dtype,
                    token=self.token or None,
                    ignore_mismatched_sizes=True,
                ).to(self.device)
                self._model_loaded = True
                logger.info(
                    f"Loaded ESMFold from {load_from} on {self.device} (dtype: {str(dtype)})"
                )
            except Exception as e:
                raise PredictionError(
                    f"Failed to load ESMFold model: {str(e)}", code="MODEL_LOAD_ERROR"
                ) from e

    def healthcheck(self) -> bool:
        """Checks the health of the provider.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            self._load_model()
            # Dummy short predict to verify
            dummy_seq = "A" * 10
            start = time.time()
            deadline = start + 2.0
            with torch.inference_mode():
                inputs = self.tokenizer(
                    [dummy_seq], return_tensors="pt", add_special_tokens=False
                ).to(self.device)
                if _time_left(deadline) <= 0:
                    return False
                self.model(**inputs)
            return True
        except Exception:
            return False

    def _check_circuit(self) -> None:
        """Checks the circuit breaker."""
        with self._lock:
            if self._circuit_open:
                if time.time() - self._opened_at < self.COOLDOWN:
                    raise PredictionError(
                        "Circuit open for local_esmfold", code="CIRCUIT_OPEN"
                    )
                # Half-open: allow this attempt; on failure, reopen
                self._circuit_open = False  # Temp reopen for probe

    def _trip_circuit(self) -> None:
        """Trips the circuit breaker."""
        with self._lock:
            self._circuit_open = True
            self._opened_at = time.time()

    @staticmethod
    def _format_atom_name(name: str, element: str) -> str:
        """Format a PDB atom name into a 4-char field.

        Args:
            name: The atom name.
            element: The element symbol.

        Returns:
            The formatted atom name (width 4), right-justified for 1-letter elements
            (and ≤3-char names), otherwise centered.
        """
        elem_len = len(element.strip())
        name_len = len(name.strip())
        if elem_len == 1 and name_len <= 3:
            return f"{name:>4s}"
        return f"{name:^4s}"

    def _positions_to_backbone_pdb(
        self,
        sequence: str,
        positions: torch.Tensor,  # (n_res, n_atoms, 3)
        plddt_res: torch.Tensor,  # (n_res,) pLDDT; accepts 0..1 or 0..100
    ) -> str:
        """Build a minimal PDB with backbone atoms (N, CA, C, O); B-factor stores pLDDT."""
        seq_len = len(sequence)
        if (
            positions.ndim != 3
            or positions.shape[0] != seq_len
            or positions.shape[2] != 3
        ):
            raise PredictionError(
                f"Expected positions (L,A,3) matching sequence length; got {tuple(positions.shape)} vs {seq_len}",
                code="INVALID_OUTPUT_SHAPE",
            )

        n_res, n_atoms, _ = positions.shape
        if n_atoms < 4:
            raise PredictionError(
                f"Need at least 4 atoms per residue (N,CA,C,O); got A={n_atoms}",
                code="INVALID_OUTPUT_SHAPE",
            )

        # Use the first 4 atoms as N, CA, C, O (true for atom14/atom37 layouts)
        backbone_idx = (0, 1, 2, 3)
        atom_names = ["N", "CA", "C", "O"]
        atom_elements = ["N", "C", "C", "O"]

        # Normalize pLDDT scale to 0..100 without torch.nanmax (works on CPU-only builds)
        finite = torch.isfinite(plddt_res)
        maxv = float(torch.max(plddt_res[finite]).item()) if finite.any() else 1.0
        plddt_scale = 100.0 if maxv <= 1.01 else 1.0

        lines = ["MODEL     1\n"]  # exact padding required
        serial = 1
        chain_id = "A"
        alt_loc = " "
        i_code = " "
        blank_col21 = " "  # column 21 is a blank in PDB format
        charge = "  "  # two spaces

        for i in range(seq_len):
            # 3-letter residue name
            try:
                res_name = seq3(sequence[i]).upper()
            except Exception:
                res_name = "UNK"
            if len(res_name) != 3:
                res_name = (res_name[:3]).rjust(3)

            res_seq = i + 1

            # per-residue pLDDT (clamped 0..100)
            p = float(plddt_res[i].item()) if torch.isfinite(plddt_res[i]) else 0.0
            ca_plddt = max(0.0, min(100.0, p * plddt_scale))

            for idx, name, element in zip(
                backbone_idx, atom_names, atom_elements, strict=False
            ):
                pos = positions[i, idx]  # (3,)
                # Skip if any coord is non-finite
                if pos.numel() != 3 or not torch.all(torch.isfinite(pos)):
                    continue

                x, y, z = (
                    float(pos[0].item()),
                    float(pos[1].item()),
                    float(pos[2].item()),
                )
                formatted_name = self._format_atom_name(name, element)  # 4-char field

                # Fixed-width ATOM record according to PDB v3.3
                line = (
                    f"ATOM  {serial:5d} {formatted_name}{alt_loc}"
                    f"{res_name:3s}{blank_col21}{chain_id}"
                    f"{res_seq:4d}{i_code}"
                    f"   "  # pad so X starts at col 31
                    f"{x:8.3f}{y:8.3f}{z:8.3f}"
                    f"{1.00:6.2f}{ca_plddt:6.2f}"
                    f"          "  # 10 spaces → element at col 77
                    f"{element:>2s}{charge}\n"
                )
                lines.append(line)
                serial += 1

        lines.append("TER\nENDMDL\n")
        return "".join(lines)

    def _to_per_res_plddt(
        self,
        plddt_any: torch.Tensor,
        n_res: int | None = None,
        n_atoms: int | None = None,
        **compat_kwargs: Any,
    ) -> torch.Tensor:
        """Normalize arbitrary pLDDT tensor to shape (n_res,) in [0, 1].

        Back-compat: also accepts kwargs ``L`` and ``A`` used in older tests.
        """
        # ---- back-compat with tests that pass L/A ----
        if n_res is None:
            n_res = compat_kwargs.get("L")
        if n_atoms is None:
            n_atoms = compat_kwargs.get("A")
        if n_res is None or n_atoms is None:
            raise TypeError("n_res/A (or compat L/A) must be provided")

        t = plddt_any

        # Peel recycle/batch dims from the front (prefer last recycle, first batch)
        if t.dim() == 5:  # (R,B,L,A,*) → (B,L,A,*) → (L,A,*)
            t = t[-1, 0]
        elif t.dim() == 4 and t.shape[0] not in (
            n_res,
            n_atoms,
        ):  # (R,B,L,A) or (B,L,A,*)
            t = t[-1]  # → (L,A,*) or (L,A)

        if t.dim() >= 3 and t.shape[0] not in (n_res, n_atoms):
            t = t[0]  # drop batch if present

        # Reduce to (n_res,)
        if t.dim() == 1:
            if t.shape[0] != n_res:
                raise PredictionError(
                    f"Unexpected 1D pLDDT length {t.shape[0]}",
                    code="INVALID_OUTPUT_SHAPE",
                )
            per_res = t

        elif t.dim() == 2:
            if t.shape[0] == n_res and t.shape[1] in (n_atoms, 14, 37):
                ca_idx = 1 if t.shape[1] in (14, 37) else (1 if n_atoms >= 2 else 0)
                per_res = t[:, ca_idx] if ca_idx < t.shape[1] else t.mean(dim=1)
            elif t.shape[1] == n_res and t.shape[0] in (n_atoms, 14, 37):
                ca_idx = 1 if t.shape[0] in (14, 37) else (1 if n_atoms >= 2 else 0)
                per_res = t[ca_idx, :] if ca_idx < t.shape[0] else t.mean(dim=0)
            elif t.shape[0] == n_res and t.shape[1] == 1:
                per_res = t[:, 0]
            else:
                raise PredictionError(
                    f"Unexpected 2D pLDDT shape {tuple(t.shape)}",
                    code="INVALID_OUTPUT_SHAPE",
                )

        elif t.dim() == 3:
            # Treat as (L, A, *) and reduce atoms/last dim
            if t.shape[0] == n_res and t.shape[1] in (n_atoms, 14, 37):
                ca_idx = 1 if t.shape[1] in (14, 37) else (1 if n_atoms >= 2 else 0)
                if ca_idx < t.shape[1]:
                    per_res = t[:, ca_idx]
                    per_res = (
                        per_res.squeeze(-1)
                        if per_res.dim() == 2 and per_res.shape[-1] == 1
                        else per_res.mean(dim=-1)
                    )
                else:
                    per_res = t.mean(dim=tuple(range(1, t.dim())))
            else:
                raise PredictionError(
                    f"Unexpected 3D pLDDT shape {tuple(t.shape)}",
                    code="INVALID_OUTPUT_SHAPE",
                )

        else:
            raise PredictionError(
                f"Unexpected pLDDT rank {t.dim()}", code="INVALID_OUTPUT_SHAPE"
            )

        # Scale to [0,1] safely
        per_res = per_res.to(dtype=torch.float32)
        finite = torch.isfinite(per_res)
        maxv = float(torch.max(per_res[finite]).item()) if finite.any() else 1.0
        if maxv > 1.01:  # values look like 0..100
            per_res = per_res / 100.0
        return per_res

    def predict(
        self, sequence: str, timeout: float = 180.0, seed: int | None = 42
    ) -> PredictionResult | None:
        """Predict the protein structure.

        Args:
            sequence: The amino acid sequence.
            timeout: The timeout in seconds.
            seed: The random seed.

        Returns:
            The prediction result.

        Raises:
            PredictionError: If prediction fails for any reason.
        """
        start_time = time.time()
        deadline = start_time + timeout
        self._check_circuit()
        if not sequence:
            raise PredictionError("Empty sequence", code="BAD_INPUT")
        max_len = int(os.getenv("ESMFOLD_MAX_LEN", "1200"))
        if len(sequence) > max_len:
            raise PredictionError(
                f"Sequence too long for local ESMFold (max: {max_len})",
                code="BAD_INPUT",
            )
        retry_device = self.device
        for attempt in range(2):  # Try CUDA, then CPU on OOM
            self.device = retry_device
            try:
                if _time_left(deadline) <= 0:
                    raise PredictionError("Timeout before model load", code="TIMEOUT")
                self._load_model()
                if _time_left(deadline) <= 0:
                    raise PredictionError("Timeout during model load", code="TIMEOUT")
                # ---- Inference ---------------------------------------------------
                with self._infer_lock:
                    if seed is not None:
                        torch.manual_seed(seed)
                    if torch.cuda.is_available():
                        torch.backends.cudnn.deterministic = True
                        torch.backends.cudnn.benchmark = False
                    inputs = self.tokenizer(
                        [sequence],
                        return_tensors="pt",
                        add_special_tokens=False,
                        return_attention_mask=True,
                    ).to(self.device)
                    if _time_left(deadline) <= 0:
                        raise PredictionError(
                            "Timeout after tokenization", code="TIMEOUT"
                        )
                    with torch.inference_mode():
                        if self.device == "cuda":
                            with torch.cuda.amp.autocast():
                                outputs = self.model(**inputs)  # type: ignore[operator]
                        else:
                            outputs = self.model(**inputs)  # type: ignore[operator]
                    if _time_left(deadline) <= 0:
                        raise PredictionError("Timeout after inference", code="TIMEOUT")
                # ---- Normalize model outputs ------------------------------------
                pos_any = getattr(outputs, "positions", None)
                plddt_any = getattr(outputs, "plddt", None)
                if pos_any is None or plddt_any is None:
                    raise PredictionError(
                        "Model output missing 'positions' or 'plddt'. Likely library incompatibility.",
                        code="INVALID_OUTPUT",
                    )
                # positions -> (L, A, 3)
                if pos_any.dim() == 5:  # (R, B, L, A, 3)
                    pos_any = pos_any[-1, 0]
                elif pos_any.dim() == 4:  # (B, L, A, 3)
                    pos_any = pos_any[0]
                elif pos_any.dim() == 3:  # (L, A, 3)
                    pass
                else:
                    raise PredictionError(
                        f"Unexpected positions shape: {tuple(pos_any.shape)}",
                        code="INVALID_OUTPUT_SHAPE",
                    )
                # pLDDT -> (L,)
                n_res, n_atoms, _ = pos_any.shape
                plddt_res = self._to_per_res_plddt(plddt_any, n_res, n_atoms)
                if plddt_res.shape[0] != n_res:
                    raise PredictionError(
                        f"Length mismatch: positions L={n_res} vs pLDDT L={plddt_res.shape[0]}",
                        code="INVALID_OUTPUT_SHAPE",
                    )

                # ---- Build PDB (uses first 4 atoms as N, CA, C, O) --------------
                pdb_text = self._positions_to_backbone_pdb(sequence, pos_any, plddt_res)
                # ---- Mean pLDDT on 0..100 scale (no nan* ops) ----
                finite = torch.isfinite(plddt_res)
                maxv = (
                    float(torch.max(plddt_res[finite]).item()) if finite.any() else 1.0
                )
                scale = 100.0 if maxv <= 1.01 else 1.0
                mean_plddt_val = (
                    float((plddt_res[finite] * scale).mean().item())
                    if finite.any()
                    else 0.0
                )
                with self._lock:
                    self._fail_count = 0
                raw_data = {
                    "sequence_length": len(sequence),
                    "mean_plddt": mean_plddt_val,
                    "device": self.device,
                    "latency": time.time() - start_time,
                    "seed": seed,
                }
                return PredictionResult(pdb_text, self.name, raw_data)
            except torch.cuda.OutOfMemoryError as e:
                torch.cuda.empty_cache()
                if attempt == 0 and self.device == "cuda":
                    logger.warning("OOM on CUDA; retrying on CPU")
                    retry_device = "cpu"
                    continue
                raise PredictionError(
                    "GPU OOM and CPU retry failed: Try shorter sequence or more VRAM",
                    code="OOM_ERROR",
                ) from e
            except Exception as e:
                with self._lock:
                    self._fail_count += 1
                    if self._fail_count >= self.MAX_FAILS:
                        self._trip_circuit()
                if _time_left(deadline) <= 0:
                    raise PredictionError("Inference timeout", code="TIMEOUT") from e
                raise PredictionError(
                    f"ESMFold inference failed: {str(e)}", code="INFERENCE_ERROR"
                ) from e

    def close(self) -> None:
        """Closes the provider."""
        pass
