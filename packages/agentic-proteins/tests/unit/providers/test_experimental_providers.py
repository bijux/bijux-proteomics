# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass, field
import sys
from types import SimpleNamespace
from typing import Any

import pytest
from requests.exceptions import RequestException

from agentic_proteins.providers.errors import PredictionError
from agentic_proteins.providers.experimental import _async_utils
from agentic_proteins.providers.experimental import colabfold
from agentic_proteins.providers.experimental.openprotein import APIOpenProteinProvider


def test_sleep_with_backoff_deadline_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_async_utils.time, "sleep", lambda _s: None)
    backoff, slept = _async_utils.sleep_with_backoff(deadline=0.0, backoff=1.0)
    assert backoff == 1.0
    assert slept == 0.0


def test_sleep_with_retry_after_uses_retry_after(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(_async_utils.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        _async_utils.secrets.SystemRandom, "random", lambda _self: 0.0
    )
    deadline = _async_utils.time.time() + 10.0
    backoff, slept = _async_utils.sleep_with_retry_after(
        deadline=deadline, backoff=1.0, retry_after=3.0
    )
    assert backoff > 1.0
    assert slept == 3.0


def test_sleep_with_retry_after_deadline_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_async_utils.time, "sleep", lambda _s: None)
    backoff, slept = _async_utils.sleep_with_retry_after(
        deadline=0.0, backoff=2.0, retry_after=1.0
    )
    assert backoff == 2.0
    assert slept == 0.0


@dataclass
class _FakeResponse:
    status_code: int
    payload: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)

    def json(self) -> dict[str, Any]:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RequestException(f"status={self.status_code}")


class _FakeSession:
    def __init__(self, post_response: _FakeResponse, get_response: _FakeResponse) -> None:
        self._post_response = post_response
        self._get_response = get_response
        self.headers: dict[str, str] = {}

    def mount(self, *_args, **_kwargs) -> None:
        return None

    def post(self, *_args, **_kwargs) -> _FakeResponse:
        return self._post_response

    def get(self, *_args, **_kwargs) -> _FakeResponse:
        return self._get_response

    def close(self) -> None:
        return None


def test_colabfold_predict_success(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=200, payload={"job_id": "job-1"})
    poll = _FakeResponse(
        status_code=200,
        payload={"status": "SUCCESS", "result": {"models": [{"pdb": "PDB"}]}},
    )
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    monkeypatch.setattr(colabfold, "sleep_with_backoff", lambda *args, **kwargs: (1.0, 0.0))
    monkeypatch.setattr(
        colabfold, "sleep_with_retry_after", lambda *args, **kwargs: (1.0, 0.0)
    )
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    result = provider.predict("ACD", timeout=5.0)
    assert result.provider == provider.name
    assert result.pdb_text == "PDB"


def test_colabfold_healthcheck_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=200, payload={})
    poll = _FakeResponse(status_code=200, payload={})
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    assert provider.healthcheck() is True


def test_colabfold_healthcheck_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FailSession(_FakeSession):
        def get(self, *_args, **_kwargs):
            raise RequestException("down")

    post = _FakeResponse(status_code=200, payload={"job_id": "job-1"})
    poll = _FakeResponse(status_code=200, payload={})
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FailSession(post, poll))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    assert provider.healthcheck() is False


def test_colabfold_predict_missing_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=200, payload={"status": "ok"})
    poll = _FakeResponse(status_code=200, payload={})
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    with pytest.raises(PredictionError, match="job_id"):
        provider.predict("ACD", timeout=5.0)


def test_colabfold_predict_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BadResponse(_FakeResponse):
        def json(self) -> dict[str, Any]:
            raise ValueError("bad json")

    post = _BadResponse(status_code=200, payload={})
    poll = _FakeResponse(status_code=200, payload={})
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    with pytest.raises(PredictionError, match="Invalid JSON"):
        provider.predict("ACD", timeout=5.0)


def test_colabfold_predict_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=401, payload={})
    poll = _FakeResponse(status_code=500, payload={})
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    with pytest.raises(PredictionError, match="Authentication failed"):
        provider.predict("ACD", timeout=5.0)


def test_colabfold_predict_missing_status(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=200, payload={"job_id": "job-4"})
    poll = _FakeResponse(status_code=200, payload={"result": {}})
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    monkeypatch.setattr(colabfold, "sleep_with_backoff", lambda *args, **kwargs: (1.0, 0.0))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    with pytest.raises(PredictionError, match="No status"):
        provider.predict("ACD", timeout=5.0)


def test_colabfold_predict_missing_pdb(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=200, payload={"job_id": "job-5"})
    poll = _FakeResponse(
        status_code=200,
        payload={"status": "SUCCESS", "result": {"models": [{"pdb": 123}]}},
    )
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    monkeypatch.setattr(colabfold, "sleep_with_backoff", lambda *args, **kwargs: (1.0, 0.0))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    with pytest.raises(PredictionError, match="No PDB string"):
        provider.predict("ACD", timeout=5.0)


def test_colabfold_predict_empty_pdb(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=200, payload={"job_id": "job-6"})
    poll = _FakeResponse(
        status_code=200,
        payload={"status": "SUCCESS", "result": {"models": [{"pdb": ""}]}},
    )
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    monkeypatch.setattr(colabfold, "sleep_with_backoff", lambda *args, **kwargs: (1.0, 0.0))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    with pytest.raises(PredictionError, match="Empty PDB"):
        provider.predict("ACD", timeout=5.0)


def test_colabfold_predict_request_id(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(
        status_code=200, payload={"job_id": "job-7"}, headers={"x-request-id": "req-1"}
    )
    poll = _FakeResponse(
        status_code=200,
        payload={"status": "SUCCESS", "result": {"models": [{"pdb": "PDB"}]}},
        headers={"x-request-id": "req-2"},
    )
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    monkeypatch.setattr(colabfold, "sleep_with_backoff", lambda *args, **kwargs: (1.0, 0.0))
    monkeypatch.setattr(
        colabfold, "sleep_with_retry_after", lambda *args, **kwargs: (1.0, 0.0)
    )
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    result = provider.predict("ACD", timeout=5.0, seed=7)
    assert result.raw["request_id"] == "req-2"
    assert result.raw["seed"] == 7


def test_colabfold_rate_limit_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=429, payload={}, headers={"Retry-After": "1"})
    poll = _FakeResponse(status_code=200, payload={})

    class _RetrySession(_FakeSession):
        def post(self, *_args, **_kwargs) -> _FakeResponse:
            return self._post_response

    monkeypatch.setattr(colabfold.requests, "Session", lambda: _RetrySession(post, poll))
    monkeypatch.setattr(colabfold, "_time_left", lambda _deadline: 10.0)
    monkeypatch.setattr(
        colabfold, "sleep_with_retry_after", lambda *args, **kwargs: (1.0, 0.0)
    )
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    with pytest.raises(PredictionError, match="ColabFold post failed after retries"):
        provider.predict("ACD", timeout=5.0)


def test_openprotein_predict_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Job:
        def wait_for_pdb(self, timeout: float = 0.0) -> str:
            return "PDB"

    class _FoldNamespace:
        def esmfold(self, sequence: str) -> _Job:
            return _Job()

    class _Session:
        fold = _FoldNamespace()

    fake_module = SimpleNamespace(connect=lambda username, password: _Session())
    monkeypatch.setitem(sys.modules, "openprotein", fake_module)

    provider = APIOpenProteinProvider(user="user", password="pw", model="esmfold")
    result = provider.predict("ACDE", timeout=1.0)
    assert result.provider == provider.name
    assert result.pdb_text == "PDB"


def test_openprotein_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENPROTEIN_USER", raising=False)
    monkeypatch.delenv("OPENPROTEIN_PASSWORD", raising=False)
    with pytest.raises(ValueError, match="OPENPROTEIN_USER"):
        APIOpenProteinProvider(user=None, password=None)


def test_openprotein_has_attr_handles_exception() -> None:
    class _Boom:
        def __getattr__(self, _name):
            raise RuntimeError("boom")

    assert APIOpenProteinProvider._has_attr(_Boom(), "fold") is False


def test_openprotein_debug_dump_handles_exception() -> None:
    class _Boom:
        def __dir__(self):
            raise RuntimeError("boom")

    assert APIOpenProteinProvider._debug_dump(_Boom()) == "<dir() failed>"


def test_openprotein_resolve_model_maps_alias() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)
    provider.model = "alphafold"
    assert provider._resolve_model() == "af2"


def test_openprotein_pick_submit_fn_direct() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)
    provider.model = "esmfold"

    class _NS:
        def esmfold(self, sequence: str) -> str:
            return sequence

    fn, kw = provider._pick_submit_fn(_NS(), SimpleNamespace())
    assert callable(fn)
    assert "sequence" in kw


def test_openprotein_pick_submit_fn_get_model() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)
    provider.model = "esmfold"

    class _Model:
        def submit(self, sequence: str) -> str:
            return sequence

    class _NS:
        def get_model(self, _name: str) -> _Model:
            return _Model()

    fn, kw = provider._pick_submit_fn(_NS(), SimpleNamespace())
    assert callable(fn)
    assert "sequence" in kw


def test_openprotein_wait_and_get_pdb_from_results_dict() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)

    class _Fold:
        def get_results(self, _job_id: str):
            return {"models": [{"pdb": "PDB"}]}

    provider.session = SimpleNamespace(fold=_Fold())

    class _Job:
        job_id = "job-1"

    assert provider._wait_and_get_pdb(_Job(), timeout=1.0) == "PDB"


def test_openprotein_wait_and_get_pdb_from_job_method() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)

    class _Job:
        def get_pdb(self) -> str:
            return "PDB"

    provider.session = SimpleNamespace()
    assert provider._wait_and_get_pdb(_Job(), timeout=1.0) == "PDB"


def test_openprotein_wait_and_get_pdb_wait_session() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)

    class _Fold:
        def get_results(self, _job_id: str):
            return {"pdb_text": "PDB"}

    class _Session:
        fold = _Fold()

        def wait_until_done(self, *_args, **_kwargs) -> None:
            raise TypeError("bad args")

    provider.session = _Session()

    class _Job:
        job_id = "job-9"

    assert provider._wait_and_get_pdb(_Job(), timeout=1.0) == "PDB"


def test_openprotein_wait_and_get_pdb_session_handle() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)

    class _Handle:
        def get_results(self):
            return {"pdb": "PDB"}

    class _Session:
        def get(self, _job_id: str):
            return _Handle()

    provider.session = _Session()

    class _Job:
        job_id = "job-10"

    assert provider._wait_and_get_pdb(_Job(), timeout=1.0) == "PDB"


def test_openprotein_wait_and_get_pdb_attr_result() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)

    class _Result:
        pdb = "PDB"

    class _Fold:
        def get_results(self, _job_id: str):
            return _Result()

    provider.session = SimpleNamespace(fold=_Fold())

    class _Job:
        job_id = "job-11"

    assert provider._wait_and_get_pdb(_Job(), timeout=1.0) == "PDB"


def test_openprotein_missing_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Session:
        pass

    fake_module = SimpleNamespace(connect=lambda username, password: _Session())
    monkeypatch.setitem(sys.modules, "openprotein", fake_module)

    provider = APIOpenProteinProvider(user="user", password="pw", model="esmfold")
    with pytest.raises(PredictionError, match="structure namespace"):
        provider.predict("ACDE", timeout=1.0)


def test_openprotein_submit_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FoldNamespace:
        def esmfold(self, sequence: str) -> str:
            raise RuntimeError("boom")

    class _Session:
        fold = _FoldNamespace()

    fake_module = SimpleNamespace(connect=lambda username, password: _Session())
    monkeypatch.setitem(sys.modules, "openprotein", fake_module)

    provider = APIOpenProteinProvider(user="user", password="pw", model="esmfold")
    with pytest.raises(PredictionError, match="submit failed"):
        provider.predict("ACDE", timeout=1.0)


def test_openprotein_pick_submit_fn_fallback_create() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)
    provider.model = "esmfold"

    class _NS:
        def create(self, sequence: str, model_name: str) -> str:
            return f"{sequence}:{model_name}"

    fn, kw = provider._pick_submit_fn(_NS(), SimpleNamespace())
    assert callable(fn)
    assert "model_name" in kw


def test_openprotein_wait_and_get_pdb_from_job_json() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)

    class _Fold:
        def get_results(self, _job_id: str):
            return {"pdb": "PDB"}

    class _Session:
        fold = _Fold()

        def wait_until_done(self, *_args, **_kwargs) -> None:
            return None

    provider.session = _Session()

    class _Job:
        def json(self) -> dict[str, str]:
            return {"job_id": "job-2"}

    assert provider._wait_and_get_pdb(_Job(), timeout=1.0) == "PDB"


def test_openprotein_predict_uses_structure_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Job:
        job_id = "job-3"

    class _Structure:
        def create(self, sequence: str, model_name: str):
            return _Job()

        def get_results(self, _job_id: str):
            return {"pdb": "PDB"}

    class _Session:
        structure = _Structure()

    fake_module = SimpleNamespace(connect=lambda username, password: _Session())
    monkeypatch.setitem(sys.modules, "openprotein", fake_module)

    provider = APIOpenProteinProvider(user="user", password="pw", model="esmfold")
    result = provider.predict("ACDE", timeout=1.0)
    assert result.pdb_text == "PDB"


def test_openprotein_predict_empty_pdb_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Job:
        def wait_for_pdb(self, timeout: float = 0.0) -> str:
            return ""

    class _FoldNamespace:
        def esmfold(self, sequence: str) -> _Job:
            return _Job()

    class _Session:
        fold = _FoldNamespace()

    fake_module = SimpleNamespace(connect=lambda username, password: _Session())
    monkeypatch.setitem(sys.modules, "openprotein", fake_module)

    provider = APIOpenProteinProvider(user="user", password="pw", model="esmfold")
    with pytest.raises(PredictionError, match="empty PDB"):
        provider.predict("ACDE", timeout=1.0)


def test_openprotein_connect_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = SimpleNamespace(connect=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setitem(sys.modules, "openprotein", fake_module)
    with pytest.raises(PredictionError, match="connect failed"):
        APIOpenProteinProvider(user="user", password="pw", model="esmfold")


def test_openprotein_pick_submit_fn_session_method() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)
    provider.model = "esmfold"

    class _Session:
        def structure_predict(self, sequence: str, model_name: str) -> str:
            return f"{sequence}:{model_name}"

    fn, kw = provider._pick_submit_fn(SimpleNamespace(), _Session())
    assert callable(fn)
    assert "model_name" in kw


def test_openprotein_wait_and_get_pdb_missing_job_id() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)
    provider.session = SimpleNamespace()

    class _Job:
        pass

    assert provider._wait_and_get_pdb(_Job(), timeout=1.0) is None


def test_openprotein_pick_submit_fn_get_model_fails_then_fallback() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)
    provider.model = "esmfold"

    class _NS:
        def get_model(self, _name: str):
            raise KeyError("missing")

        def create(self, sequence: str, model_name: str) -> str:
            return f"{sequence}:{model_name}"

    fn, kw = provider._pick_submit_fn(_NS(), SimpleNamespace())
    assert callable(fn)
    assert "model_name" in kw


def test_openprotein_pick_submit_fn_missing() -> None:
    provider = APIOpenProteinProvider.__new__(APIOpenProteinProvider)
    provider.model = "esmfold"
    with pytest.raises(PredictionError, match="No submit function"):
        provider._pick_submit_fn(SimpleNamespace(), SimpleNamespace())


def test_colabfold_poll_error_status(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=200, payload={"job_id": "job-1"})
    poll = _FakeResponse(status_code=200, payload={"status": "ERROR", "error": "fail"})
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    monkeypatch.setattr(colabfold, "sleep_with_backoff", lambda *args, **kwargs: (1.0, 0.0))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    with pytest.raises(PredictionError, match="fail"):
        provider.predict("ACD", timeout=5.0)


def test_colabfold_poll_invalid_result(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakeResponse(status_code=200, payload={"job_id": "job-2"})
    poll = _FakeResponse(status_code=200, payload={"status": "SUCCESS", "result": {}})
    monkeypatch.setattr(colabfold.requests, "Session", lambda: _FakeSession(post, poll))
    monkeypatch.setattr(colabfold, "sleep_with_backoff", lambda *args, **kwargs: (1.0, 0.0))
    provider = colabfold.APIColabFoldProvider(api_url="http://example")
    with pytest.raises(PredictionError, match="Invalid result structure"):
        provider.predict("ACD", timeout=5.0)
