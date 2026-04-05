# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""OpenProtein API provider."""

from __future__ import annotations

import os
import sys

from loguru import logger

from agentic_proteins.providers.base import (
    BaseProvider,
    PredictionResult,
    ProviderMetadata,
)
from agentic_proteins.providers.errors import PredictionError


class APIOpenProteinProvider(BaseProvider):
    """OpenProtein.ai via official client, with defensive fallbacks."""

    _MODEL_MAP = {
        "esmfold": "esmfold",
        "af2": "af2",
        "alphafold": "af2",
        "alphafold2": "af2",
    }

    def __init__(
        self,
        user: str | None = None,
        password: str | None = None,
        model: str = "esmfold",
    ) -> None:
        """Initialize an OpenProtein API provider.

        Args:
          user: Username for OpenProtein. Falls back to env ``OPENPROTEIN_USER``.
          password: Password for OpenProtein. Falls back to env ``OPENPROTEIN_PASSWORD``.
          model: Model name to use (e.g., ``"esmfold"``).

        Raises:
          ValueError: If credentials are missing.
          PredictionError: If establishing the OpenProtein session fails.
        """
        self.model = model.lower()
        self.name = f"api_openprotein_{self.model}"
        self.session = None
        self.metadata = ProviderMetadata(name=self.name, experimental=True)

        u = (user or os.getenv("OPENPROTEIN_USER") or "").strip()
        p = (password or os.getenv("OPENPROTEIN_PASSWORD") or "").strip()
        if not (u and p):
            raise ValueError("OPENPROTEIN_USER and OPENPROTEIN_PASSWORD must be set.")

        try:
            import openprotein

            self.session = openprotein.connect(username=u, password=p)
        except Exception as e:
            raise PredictionError(
                f"OpenProtein connect failed: {e}", code="AUTH_ERROR"
            ) from e

    # ----------------------------- helpers ---------------------------------

    @staticmethod
    def _has_attr(obj, name: str) -> bool:
        """Safely check attribute existence; returns False on errors."""
        try:
            return hasattr(obj, name)
        except Exception:  # noqa: BLE001
            return False

    @staticmethod
    def _debug_dump(obj) -> str:
        """Return comma-separated public attribute names for debug output."""
        try:
            return ", ".join(sorted(n for n in dir(obj) if not n.startswith("_")))
        except Exception:  # noqa: BLE001
            return "<dir() failed>"

    def _resolve_model(self) -> str:
        """Map friendly model alias to the API's canonical model id."""
        return self._MODEL_MAP.get(self.model, self.model)

    def _find_structure_namespace(self, sess):
        """Prefer new-style `sess.fold`, fall back to older `sess.structure`."""
        if self._has_attr(sess, "fold"):
            return sess.fold
        if self._has_attr(sess, "structure"):
            return sess.structure
        return None

    def _pick_submit_fn(self, ns, sess):
        """Return (callable, kwargs_template) for submitting a job.

        Tries, in order:
          1) ns.<model>(sequence=...)
          2) ns.get_model(model).{submit|predict|create|__call__}(sequence=...)
          3) ns.{create|predict|create_job|submit}(sequence=..., model_name=...)
          4) sess.{structure_predict|predict_structure}(sequence=..., model_name=...)
        """
        m = self._resolve_model()

        # (1) fold.esmfold / fold.af2 / fold.alphafold2
        if hasattr(ns, m) and callable(getattr(ns, m)):
            return getattr(ns, m), {"sequence": None}

        # (2) fold.get_model("esmfold") → submit/predict/create/__call__
        if hasattr(ns, "get_model"):
            try:
                model_obj = ns.get_model(m)
            except (AttributeError, TypeError, ValueError, KeyError) as e:
                # e.g. client without get_model, bad signature, or unknown model id
                logger.debug(f"openprotein.fold.get_model({m!r}) failed: {e!r}")
            else:
                for meth in ("submit", "predict", "create", "__call__"):
                    fn = getattr(model_obj, meth, None)
                    if callable(fn):
                        return fn, {"sequence": None}

        # (3) older structure namespace with generic submitters
        for meth in ("create", "predict", "create_job", "submit"):
            if hasattr(ns, meth) and callable(getattr(ns, meth)):
                # Most older APIs: (sequence=..., model_name=...) or (sequence=..., model=...)
                return getattr(ns, meth), {"sequence": None, "model_name": None}

        # (4) top-level convenience
        for meth in ("structure_predict", "predict_structure"):
            if hasattr(sess, meth) and callable(getattr(sess, meth)):
                return getattr(sess, meth), {"sequence": None, "model_name": None}

        raise PredictionError(
            "No submit function found in OpenProtein client.", code="CLIENT_MISMATCH"
        )

    def _wait_and_get_pdb(self, job, timeout: float) -> str | None:
        """Try job-level helpers first; else session.wait/wait_until_done then fold.get_results(job_id)."""
        # 1) Direct job methods
        for getter in ("wait_for_pdb", "result_pdb", "get_pdb", "pdb", "download_pdb"):
            fn = getattr(job, getter, None)
            if callable(fn):
                try:
                    return fn(timeout=timeout)
                except TypeError:
                    try:
                        return fn(seconds=timeout)
                    except Exception:
                        return fn()
        # 2) Fallback: wait + fetch by id
        job_id = (
            getattr(job, "job_id", None)
            or getattr(job, "id", None)
            or getattr(job, "uuid", None)
        )
        if not job_id and hasattr(job, "json"):
            try:
                j = job.json()  # type: ignore[attr-defined]
            except (AttributeError, TypeError, ValueError) as e:
                # Client may not implement .json(), or returns non-JSON/invalid
                logger.debug(f"openprotein job.json() failed: {e!r}")
            else:
                if isinstance(j, dict):
                    job_id = j.get("job_id") or j.get("id") or j.get("uuid")

        if not job_id:
            return None

        # Wait for completion (some clients want job, some want id)
        try:
            wait_done = getattr(self.session, "wait_until_done", None)
            wait_simple = getattr(self.session, "wait", None)

            if callable(wait_done):
                try:
                    # some SDKs accept the job object
                    wait_done(job, timeout=timeout)  # type: ignore[arg-type]
                except (TypeError, ValueError) as e:
                    logger.debug(
                        f"wait_until_done(job, ...) failed: {e!r}; retrying with job_id={job_id!r}"
                    )
                    try:
                        wait_done(job_id, timeout=timeout)  # type: ignore[arg-type]
                    except Exception as e2:  # keep broad here but log
                        logger.debug(f"wait_until_done(job_id, ...) failed: {e2!r}")
            elif callable(wait_simple):
                try:
                    wait_simple(job, timeout=timeout)  # type: ignore[arg-type]
                except (TypeError, ValueError) as e:
                    logger.debug(
                        f"wait(job, ...) failed: {e!r}; retrying with job_id={job_id!r}"
                    )
                    try:
                        wait_simple(job_id, timeout=timeout)  # type: ignore[arg-type]
                    except Exception as e2:
                        logger.debug(f"wait(job_id, ...) failed: {e2!r}")
            else:
                logger.debug(
                    "No wait function available on OpenProtein client (wait_until_done/wait missing)."
                )
        except Exception as e:
            # final guardrail—log, don't swallow silently
            logger.debug(f"OpenProtein wait() unexpected error: {e!r}")

        # Fetch results
        res = None
        fold_ns = getattr(self.session, "fold", None) or getattr(
            self.session, "structure", None
        )
        try:
            if (
                fold_ns
                and hasattr(fold_ns, "get_results")
                and callable(fold_ns.get_results)
            ):
                res = fold_ns.get_results(job_id)
            else:
                # Some clients return a handle via session.get(job_id) with .get_results()
                get_fn = getattr(self.session, "get", None)
                handle = get_fn(job_id) if callable(get_fn) else None
                if handle and hasattr(handle, "get_results"):
                    res = handle.get_results()
        except Exception:
            res = None

        # Extract PDB text from result shapes we’ve seen
        if isinstance(res, dict):
            # common flat keys
            for k in ("pdb", "pdb_text", "pdb_str", "pdbString", "pdb_content"):
                v = res.get(k)
                if isinstance(v, str) and v.strip():
                    return v
            # ColabFold-like shape
            models = res.get("models")
            if isinstance(models, list) and models:
                m0 = models[0]
                if isinstance(m0, dict):
                    for k in ("pdb", "pdb_text", "pdb_str"):
                        v = m0.get(k)
                        if isinstance(v, str) and v.strip():
                            return v
        elif hasattr(res, "pdb") and isinstance(res.pdb, str) and res.pdb.strip():
            return res.pdb

        return None

    # ----------------------------- main -------------------------------------

    def predict(
        self, sequence: str, timeout: float = 300.0, seed: int | None = None
    ) -> PredictionResult:
        """Submit a folding job to OpenProtein and return the predicted structure.

        Args:
          sequence: Amino-acid sequence (single chain) using the 20 standard residues.
          timeout: Soft deadline in seconds for remote job completion and polling.
          seed: Optional seed recorded in the result metadata (not all backends use it).

        Returns:
          PredictionResult: Wrapper containing the PDB text, provider name, and
          metadata such as job id and latency.

        Raises:
          PredictionError: If authentication/session is missing, the client API
            surface is incompatible (no structure/fold namespace or submit
            function found), submission fails remotely, the job times out, or the
            job completes without a PDB payload.
          ValueError: Propagated if critical inputs are invalid (rare; most input
            issues are normalized before submission).
        """
        if not self.session:
            raise PredictionError("OpenProtein session is None", code="AUTH_ERROR")

        import time as _t

        start = _t.time()

        ns = self._find_structure_namespace(self.session)
        if ns is None:
            sys.stderr.write(
                "OpenProtein client API mismatch: no structure/fold namespace found.\n"
                f"Session attrs: {self._debug_dump(self.session)}\n"
                "Please upgrade `openprotein-python`.\n"
            )
            raise PredictionError(
                "Client lacks structure namespace", code="CLIENT_MISMATCH"
            )

        # Find submit function
        try:
            submit_fn, kw = self._pick_submit_fn(ns, self.session)
        except PredictionError:
            sys.stderr.write(
                "OpenProtein client API mismatch: could not find submit function.\n"
                f"Namespace attrs: {self._debug_dump(ns)}\n"
                f"Session attrs:   {self._debug_dump(self.session)}\n"
                "Please upgrade `openprotein-python`.\n"
            )
            raise

        # Fill kwargs
        if "sequence" in kw:
            kw["sequence"] = sequence
        elif "seq" in kw:
            kw["seq"] = sequence

        resolved = self._resolve_model()
        if "model_name" in kw:
            kw["model_name"] = resolved
        elif "model" in kw:
            kw["model"] = resolved
        elif "modelId" in kw:
            kw["modelId"] = resolved

        if any(k in kw for k in ("payload", "data", "input")):
            payload = {"sequence": sequence, "model": resolved}
            for k in ("payload", "data", "input"):
                if k in kw:
                    kw[k] = payload

        # Submit
        try:
            try:
                job = submit_fn(**kw)
            except TypeError:
                job = submit_fn(sequence, resolved)  # positional fallback
        except Exception as e:
            raise PredictionError(
                f"OpenProtein submit failed: {e}", code="REMOTE_ERROR"
            ) from e

        # Wait + fetch PDB
        pdb_text = self._wait_and_get_pdb(job, timeout=timeout)
        if not pdb_text or not pdb_text.strip():
            raise PredictionError(
                "OpenProtein job returned empty PDB.", code="NO_OUTPUT"
            )

        return PredictionResult(
            pdb_text,
            self.name,
            {
                "job_id": getattr(job, "job_id", None)
                or getattr(job, "id", None)
                or getattr(job, "uuid", None),
                "latency": _t.time() - start,
                "seed": seed,
            },
        )
