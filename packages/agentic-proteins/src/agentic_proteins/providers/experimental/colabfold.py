# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""ColabFold API provider."""

from __future__ import annotations

import os
import threading
import time
from typing import Any

from loguru import logger
import requests  # type: ignore[import-untyped]
from requests.adapters import HTTPAdapter  # type: ignore[import-untyped]
from requests.exceptions import RequestException  # type: ignore[import-untyped]
from urllib3.util.retry import Retry

from agentic_proteins.providers.base import (
    BaseProvider,
    PredictionResult,
    ProviderMetadata,
    _time_left,
)
from agentic_proteins.providers.errors import PredictionError
from agentic_proteins.providers.experimental._async_utils import (
    sleep_with_backoff,
    sleep_with_retry_after,
)


class APIColabFoldProvider(BaseProvider):
    """API ColabFold provider."""

    name = "api_colabfold"
    metadata = ProviderMetadata(name=name, experimental=True)
    _http_lock = threading.Lock()

    def __init__(
        self,
        api_url: str = "https://api.colabfold.com/prediction/v1",
        token: str | None = None,
    ) -> None:
        """Initializes the APIColabFoldProvider.

        Args:
            api_url: The API URL.
            token: The token.
        """
        self.api_url = api_url
        self.token = (
            token
            or os.getenv("COLABFOLD_TOKEN")
            or os.getenv("COLABFOLD_API_KEY")
            or ""
        ).strip()
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.session = requests.Session()  # type: ignore[attr-defined]
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=True,
            allowed_methods=None,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update(
            {
                "User-Agent": "agentic-proteins/0.1 (+https://github.com/example/agentic-proteins)"
            }
        )

    def close(self) -> None:
        """Closes the session."""
        self.session.close()

    def healthcheck(self) -> bool:
        """Checks the health of the provider.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            r = self.session.get(self.api_url, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

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
        payload = {"sequences": [sequence], "use_templates": False, "num_recycles": 3}
        now = time.time()
        if now >= deadline:
            raise PredictionError("Timeout before start", code="TIMEOUT")
        per_timeout = (3.05, max(1.0, min(10.0, _time_left(deadline) - 0.5)))
        backoff = 1.0
        post_retries = 0
        backoff_total = 0.0
        while _time_left(deadline) > 0:
            with self._http_lock:
                try:
                    response = self.session.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload,
                        timeout=per_timeout,
                    )
                    if response.status_code == 401:
                        raise PredictionError(
                            "Authentication failed; check token/credentials",
                            code="AUTH_ERROR",
                        )
                    if response.status_code == 413:
                        raise PredictionError(
                            "Sequence too long for ColabFold; check provider limits",
                            code="BAD_INPUT",
                        )
                    response.raise_for_status()
                    break
                except RequestException as e:
                    post_retries += 1
                    retry_after = (
                        int(response.headers.get("Retry-After", 0))
                        if "response" in locals() and response.status_code in [429, 503]
                        else 0
                    )
                    logger.warning(
                        f"ColabFold post failed (retry {post_retries}): {str(e)}"
                    )
                    remaining = _time_left(deadline)
                    if remaining <= 0 or post_retries >= 5:
                        code = (
                            "RATE_LIMIT"
                            if response.status_code == 429
                            else "REMOTE_ERROR"
                            if response.status_code >= 500
                            else "UNKNOWN"
                        )
                        raise PredictionError(
                            f"ColabFold post failed after retries: {str(e)}", code=code
                        ) from e
                    backoff, slept = sleep_with_retry_after(
                        deadline, backoff, retry_after
                    )
                    backoff_total += slept
        try:
            job_data = response.json()
        except ValueError as err:
            raise PredictionError(
                "Invalid JSON response from ColabFold API", code="INVALID_OUTPUT"
            ) from err
        if "job_id" not in job_data:
            raise PredictionError("No job_id in ColabFold response", code="NO_OUTPUT")
        job_id = job_data["job_id"]
        backoff = 1.0
        raw_data: dict[str, Any] = {
            "job_id": job_id,
            "retries": 0,
            "post_retries": post_retries,
            "backoff_total_sec": backoff_total,
        }
        if "x-request-id" in response.headers:
            raw_data["request_id"] = response.headers["x-request-id"]
        while _time_left(deadline) > 0:
            try:
                now = time.time()
                if now >= deadline:
                    raise PredictionError(
                        f"ColabFold API timed out (job_id={job_id})", code="TIMEOUT"
                    )
                per_timeout = (3.05, max(1.0, min(15.0, _time_left(deadline) - 0.5)))
                with self._http_lock:
                    poll_response = self.session.get(
                        f"{self.api_url}/{job_id}",
                        headers=self.headers,
                        timeout=per_timeout,
                    )
                if poll_response.status_code in [500, 502, 503, 504]:
                    raw_data["retries"] += 1
            except RequestException as ex:
                logger.warning(f"ColabFold poll failed: {str(ex)}")
                remaining = _time_left(deadline)
                if remaining <= 0:
                    raise PredictionError(
                        f"ColabFold API timed out (job_id={job_id})", code="TIMEOUT"
                    ) from ex
                backoff, slept = sleep_with_backoff(deadline, backoff)
                backoff_total += slept
                continue
            if poll_response.status_code == 200:
                try:
                    data = poll_response.json()
                except ValueError:
                    logger.warning("Invalid JSON from ColabFold poll; retrying")
                    backoff, slept = sleep_with_backoff(deadline, backoff)
                    backoff_total += slept
                    continue
                if "status" not in data:
                    raise PredictionError(
                        "No status in ColabFold response", code="INVALID_OUTPUT"
                    )
                status = data["status"].upper()
                raw_data["last_status"] = status
                if status in {"SUCCESS", "DONE"}:
                    if (
                        "result" not in data
                        or not isinstance(data["result"], dict)
                        or "models" not in data["result"]
                        or not isinstance(data["result"]["models"], list)
                        or len(data["result"]["models"]) == 0
                    ):
                        raise PredictionError(
                            "Invalid result structure in ColabFold response: "
                            + data.get("error", "unknown error"),
                            code="INVALID_OUTPUT",
                        )
                    model = data["result"]["models"][0]
                    if "pdb" not in model or not isinstance(model["pdb"], str):
                        raise PredictionError(
                            "No PDB string in ColabFold model", code="NO_OUTPUT"
                        )
                    pdb_text = model["pdb"]
                    if not pdb_text:
                        raise PredictionError(
                            "Empty PDB in ColabFold result", code="NO_OUTPUT"
                        )
                    if "x-request-id" in poll_response.headers:
                        raw_data["request_id"] = poll_response.headers["x-request-id"]
                    raw_data["latency"] = time.time() - start_time
                    raw_data["backoff_total_sec"] = backoff_total
                    raw_data["seed"] = seed
                    logger.info(
                        f"ColabFold success: job_id={job_id}, retries={raw_data['retries']}, post_retries={post_retries}, backoff_total_sec={backoff_total}"
                    )
                    return PredictionResult(pdb_text, self.name, raw_data)
                if status in {"ERROR", "FAILED"}:
                    raise PredictionError(
                        data.get("error", "ColabFold job failed"), code="REMOTE_ERROR"
                    )
            backoff, slept = sleep_with_backoff(deadline, backoff)
            backoff_total += slept
        raise PredictionError(
            f"ColabFold API timed out (job_id={job_id})", code="TIMEOUT"
        )
