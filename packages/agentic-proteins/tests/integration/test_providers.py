# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import os
import subprocess
import types
from pathlib import Path
import sys
import time

import pytest
import requests

try:
    import torch
except ImportError:  # pragma: no cover - optional dependency
    torch = None


@pytest.fixture(scope="function")
def providers_module(monkeypatch):
    """Import provider modules and mock torch/cuda for determinism."""
    if torch is None:
        pytest.skip("torch not installed; provider tests require optional dependencies")
    import types

    from agentic_proteins.providers import base as providers_base
    from agentic_proteins.providers import errors as providers_errors
    from agentic_proteins.providers.local import esmfold as providers_esmfold
    from agentic_proteins.providers.experimental import colabfold as providers_colabfold
    from agentic_proteins.providers.experimental import openprotein as providers_openprotein
    from agentic_proteins.providers.local import rosettafold as providers_rosettafold

    # Mock transformers if not installed
    mock_transformers = types.ModuleType("transformers")
    monkeypatch.setitem(sys.modules, "transformers", mock_transformers)

    # Inject real torch into ESMFold module
    monkeypatch.setattr(providers_esmfold, "torch", torch)

    # Mock cuda
    mock_cuda = types.SimpleNamespace(
        is_available=lambda: False,
        _is_in_bad_fork=lambda: False,
        OutOfMemoryError=RuntimeError,
        amp=types.SimpleNamespace(
            autocast=lambda dtype=None, enabled=True: types.SimpleNamespace(
                __enter__=lambda: None, __exit__=lambda *_args: False
            )
        ),
        empty_cache=lambda: None,
    )
    monkeypatch.setattr(torch, "cuda", mock_cuda)

    mock_backends = types.SimpleNamespace(
        cudnn=types.SimpleNamespace(deterministic=True, benchmark=False)
    )
    monkeypatch.setattr(torch, "backends", mock_backends)

    providers = types.SimpleNamespace(
        PredictionError=providers_errors.PredictionError,
        PredictionResult=providers_base.PredictionResult,
        BaseProvider=providers_base.BaseProvider,
        _time_left=providers_base._time_left,
        LocalESMFoldProvider=providers_esmfold.LocalESMFoldProvider,
        LocalRoseTTAFoldProvider=providers_rosettafold.LocalRoseTTAFoldProvider,
        APIOpenProteinProvider=providers_openprotein.APIOpenProteinProvider,
        APIColabFoldProvider=providers_colabfold.APIColabFoldProvider,
        time=providers_base.time,
        shutil=providers_rosettafold.shutil,
        os=providers_rosettafold.os,
        subprocess=providers_rosettafold.subprocess,
        base=providers_base,
        esmfold=providers_esmfold,
        rosettafold=providers_rosettafold,
        openprotein=providers_openprotein,
        colabfold=providers_colabfold,
    )
    yield providers

    # Cleanup
    sys.modules.pop("transformers", None)


# Tests: Base & helpers

def test_prediction_error_and_result(providers_module):
    P = providers_module
    e = P.PredictionError("x", code="Y")
    assert isinstance(e, RuntimeError) and e.code == "Y"
    r = P.PredictionResult("PDB", "prov", {"k": 1})
    assert r.pdb_text == "PDB" and r.provider == "prov" and r.raw["k"] == 1


def test_time_left(providers_module, monkeypatch):
    P = providers_module
    clk = time.time()
    monkeypatch.setattr(P.base.time, "time", lambda: clk)
    d = clk + 10.0
    assert 9.9 <= P._time_left(d) <= 10.0
    monkeypatch.setattr(P.base.time, "time", lambda: clk + 12.0)
    assert P._time_left(d) == 0.0


# LocalESMFold: init & utils

def test_local_esm_init(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider(model_path="models/esmfold")
    assert prov.name == "local_esmfold"
    assert prov.device == "cpu"  # since we mocked cuda to False


def test_positions_to_backbone_pdb_errors(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    # wrong rank
    with pytest.raises(P.PredictionError) as ei:
        prov._positions_to_backbone_pdb("AAAA", torch.tensor([1, 2, 3]), torch.tensor([0.9] * 4))
    assert ei.value.code == "INVALID_OUTPUT_SHAPE"
    # wrong shape L mismatch
    with pytest.raises(P.PredictionError) as ei:
        pos = torch.tensor([[[0.0, 0.0, 0.0]]])  # (1,1,3) but seq len 2
        prov._positions_to_backbone_pdb("AA", pos, torch.tensor([0.9, 0.9]))
    assert ei.value.code == "INVALID_OUTPUT_SHAPE"
    # less than 4 atoms
    with pytest.raises(P.PredictionError) as ei:
        pos = torch.tensor([[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]] for _ in range(2)])  # (2,3,3)
        prov._positions_to_backbone_pdb("AA", pos, torch.tensor([0.9, 0.9]))
    assert ei.value.code == "INVALID_OUTPUT_SHAPE"


def test_positions_to_backbone_pdb_success(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    # (L=2, A=4, 3)
    pos = torch.tensor([[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]],
                        [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]])
    pld = torch.tensor([0.95, 0.5])
    pdb = prov._positions_to_backbone_pdb("AA", pos, pld)
    assert "ATOM" in pdb and "MODEL" in pdb and "ENDMDL" in pdb
    assert "95.00" in pdb  # scaled plddt
    assert "50.00" in pdb


def test_positions_to_backbone_pdb_non_finite_skips_atom(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    pos = torch.tensor([[[0.0, 0.0, 0.0], [float('nan'), 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]])
    pld = torch.tensor([0.9])
    pdb = prov._positions_to_backbone_pdb("A", pos, pld)
    assert pdb.count("ATOM") == 3  # skipped the nan coord atom


def test_positions_to_backbone_pdb_plddt_scale(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    pos = torch.tensor([[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]])
    # 0..100 scale
    pld = torch.tensor([90.0])
    pdb = prov._positions_to_backbone_pdb("A", pos, pld)
    assert "90.00" in pdb
    # 0..1 scale
    pld = torch.tensor([0.9])
    pdb = prov._positions_to_backbone_pdb("A", pos, pld)
    assert "90.00" in pdb
    # non-finite plddt -> 0.0
    pld = torch.tensor([float('nan')])
    pdb = prov._positions_to_backbone_pdb("A", pos, pld)
    assert " 0.00" in pdb


# _to_per_res_plddt shapes

def test_to_per_res_plddt_1d_ok(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    t = torch.tensor([0.5, 0.6, 0.7])
    out = prov._to_per_res_plddt(t, L=3, A=4)
    assert out.shape == (3,)
    assert torch.allclose(out, torch.tensor([0.5, 0.6, 0.7]))


def test_to_per_res_plddt_1d_bad(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    t = torch.tensor([0.5, 0.6])
    with pytest.raises(P.PredictionError) as ei:
        prov._to_per_res_plddt(t, L=3, A=4)
    assert ei.value.code == "INVALID_OUTPUT_SHAPE"


def test_to_per_res_plddt_2d_atom_last(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    # (L=3, A=4)
    t = torch.tensor([[0.1, 0.2, 0.3, 0.4],
                      [0.5, 0.6, 0.7, 0.8],
                      [0.9, 1.0, 1.0, 1.0]])
    out = prov._to_per_res_plddt(t, L=3, A=4)
    assert out.shape == (3,)
    assert torch.allclose(out, torch.tensor([0.2, 0.6, 1.0]))  # CA idx=1


def test_to_per_res_plddt_2d_transposed(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    # (A=4, L=3)
    t = torch.tensor([[0.1, 0.5, 0.9],
                      [0.2, 0.6, 1.0],
                      [0.3, 0.7, 1.0],
                      [0.4, 0.8, 1.0]])
    out = prov._to_per_res_plddt(t, L=3, A=4)
    assert out.shape == (3,)
    assert torch.allclose(out, torch.tensor([0.2, 0.6, 1.0]))  # CA idx=1


def test_to_per_res_plddt_2d_singleton_trailing(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    t = torch.tensor([[0.1], [0.5], [0.9]])
    out = prov._to_per_res_plddt(t, L=3, A=1)
    assert out.shape == (3,)
    assert torch.allclose(out, torch.tensor([0.1, 0.5, 0.9]))


def test_to_per_res_plddt_2d_bad_shape(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    t = torch.tensor([[0.1, 0.2], [0.3, 0.4]])
    with pytest.raises(P.PredictionError) as ei:
        prov._to_per_res_plddt(t, L=3, A=4)
    assert ei.value.code == "INVALID_OUTPUT_SHAPE"


def test_to_per_res_plddt_3d_ok(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    # (L=2, A=4, 1) -> squeeze to (L, A) then CA
    t = torch.tensor([[[0.1], [0.2], [0.3], [0.4]],
                      [[0.5], [0.6], [0.7], [0.8]]])
    out = prov._to_per_res_plddt(t, L=2, A=4)
    assert out.shape == (2,)
    assert torch.allclose(out, torch.tensor([0.2, 0.6]))


def test_to_per_res_plddt_3d_mean_if_no_ca(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    # (L=2, A=3, 1) -> mean over atoms since A not 14/37, ca_idx=1 ok
    t = torch.tensor([[[0.1], [0.2], [0.3]],
                      [[0.5], [0.6], [0.7]]])
    out = prov._to_per_res_plddt(t, L=2, A=3)
    assert torch.allclose(out, torch.tensor([0.2, 0.6]))  # CA=0.2,0.6


def test_to_per_res_plddt_3d_bad(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    t = torch.tensor([[[0.1], [0.2]]])  # shape mismatch
    with pytest.raises(P.PredictionError) as ei:
        prov._to_per_res_plddt(t, L=1, A=4)
    assert ei.value.code == "INVALID_OUTPUT_SHAPE"


def test_to_per_res_plddt_rank_bad(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    t = torch.tensor([[[[0.1]]]])  # rank 4 unexpected
    with pytest.raises(P.PredictionError) as ei:
        prov._to_per_res_plddt(t, L=1, A=4)
    assert ei.value.code == "INVALID_OUTPUT_SHAPE"


def test_to_per_res_plddt_scale_and_finite(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    t = torch.tensor([50.0, float('nan'), 100.0])
    out = prov._to_per_res_plddt(t, L=3, A=1)
    expected = torch.tensor([0.5, float('nan'), 1.0])
    assert out.shape == expected.shape
    assert torch.allclose(out, expected, equal_nan=True)


def test_to_per_res_plddt_5d_recycle_batch(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    # (R=2, B=1, L=3, A=4, 1) -> last recycle, first batch, squeeze -> (L,A) -> CA
    t = torch.ones((2, 1, 3, 4, 1)) * 0.5
    t[-1, 0, :, 1, 0] = torch.tensor([0.1, 0.2, 0.3])  # CA values
    out = prov._to_per_res_plddt(t, L=3, A=4)
    assert torch.allclose(out, torch.tensor([0.1, 0.2, 0.3]))


def test_to_per_res_plddt_4d_peel(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    # (R=2, B=1, L=3, A=4) -> (L,A)
    t = torch.ones((2, 1, 3, 4)) * 0.5
    t[-1, 0, :, 1] = torch.tensor([0.1, 0.2, 0.3])
    out = prov._to_per_res_plddt(t, L=3, A=4)
    assert torch.allclose(out, torch.tensor([0.1, 0.2, 0.3]))


# LocalESMFold: healthcheck & load

def test_local_esm_healthcheck_failure(providers_module, monkeypatch):
    P = providers_module
    prov = P.LocalESMFoldProvider()

    def raise_exc():
        raise Exception("bad")

    monkeypatch.setattr(prov, "_load_model", raise_exc)
    assert prov.healthcheck() is False


def test_local_esm_load_model_success(providers_module, monkeypatch):
    P = providers_module
    prov = P.LocalESMFoldProvider(model_path="fake")

    # Mock classes
    class MockTok:
        @classmethod
        def from_pretrained(cls, *a, **k):
            return "tok"

    class MockModel:
        @classmethod
        def from_pretrained(cls, *a, **k):
            m = MockModel()
            m.to = lambda d: m
            return m

    sys.modules["transformers"].EsmTokenizer = MockTok
    sys.modules["transformers"].EsmForProteinFolding = MockModel

    monkeypatch.setattr(os.path, "exists", lambda p: False)

    prov._load_model()
    assert prov._model_loaded is True


def test_local_esm_load_model_failure(providers_module, monkeypatch):
    P = providers_module
    prov = P.LocalESMFoldProvider()

    def raise_exc(*a, **k):
        raise Exception("load fail")

    sys.modules["transformers"].EsmForProteinFolding = types.SimpleNamespace(from_pretrained=raise_exc)

    with pytest.raises(P.PredictionError) as ei:
        prov._load_model()
    assert ei.value.code == "MODEL_LOAD_ERROR"


# predict() main paths

def test_local_esm_predict_empty_sequence(providers_module):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    with pytest.raises(P.PredictionError) as ei:
        prov.predict("", timeout=1.0)
    assert ei.value.code == "BAD_INPUT"


def test_local_esm_predict_too_long(providers_module, monkeypatch):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    monkeypatch.setenv("ESMFOLD_MAX_LEN", "3")
    with pytest.raises(P.PredictionError) as ei:
        prov.predict("AAAA", timeout=1.0)
    assert ei.value.code == "BAD_INPUT"


def test_local_esm_circuit_breaker(providers_module, monkeypatch):
    P = providers_module
    prov = P.LocalESMFoldProvider()
    def mock_infer(**k):
        raise RuntimeError("boom")
    prov.model = mock_infer
    prov.tokenizer = lambda *a, **k: {"input_ids": torch.tensor([[1]]), "attention_mask": torch.tensor([[1]])}
    prov._model_loaded = True
    for _ in range(prov.MAX_FAILS):
        with pytest.raises(P.PredictionError):
            prov.predict("A", timeout=5)
    # Circuit open
    with pytest.raises(P.PredictionError) as ei:
        prov.predict("A", timeout=5)
    assert ei.value.code == "CIRCUIT_OPEN"
    # Cooldown
    monkeypatch.setattr(P.time, "time", lambda: prov._opened_at + prov.COOLDOWN + 1)
    # Half-open, but fail again, reopens
    with pytest.raises(P.PredictionError):
        prov.predict("A", timeout=5)
    assert prov._circuit_open is True

# LocalRoseTTAFold----

def test_rosetta_init_requires_docker_when_enabled(providers_module, monkeypatch):
    P = providers_module
    monkeypatch.setattr(P.shutil, "which", lambda x: None)
    with pytest.raises(ValueError):
        P.LocalRoseTTAFoldProvider(docker=True)



def test_rosetta_healthcheck_docker_false_path(providers_module, monkeypatch, tmp_path):
    P = providers_module
    monkeypatch.setattr(P.os.path, "exists", lambda p: True if "rf.py" in str(p) else False)
    monkeypatch.setattr(P.os, "access", lambda p, m: True)
    r = P.LocalRoseTTAFoldProvider(docker=False, executable=str(tmp_path / "rf.py"), weights_path=str(tmp_path / "w.pt"))
    (tmp_path / "rf.py").touch()
    (tmp_path / "w.pt").touch()
    assert r.healthcheck() is True


def test_rosetta_healthcheck_docker_true_success(providers_module, monkeypatch):
    P = providers_module
    r = P.LocalRoseTTAFoldProvider(docker=True, weights_path="w.pt")
    monkeypatch.setattr(P.shutil, "which", lambda x: "/usr/bin/docker" if x == "docker" else None)
    monkeypatch.setattr(P.os, "access", lambda p, m: True)

    def mock_run(cmd, *_args, **_kwargs):
        if "inspect" in cmd or "nvidia-smi" in cmd or "touch" in cmd:
            return types.SimpleNamespace(returncode=0)
        raise Exception("unexpected cmd")

    monkeypatch.setattr(P.subprocess, "run", mock_run)
    assert r.healthcheck() is True


def test_rosetta_healthcheck_docker_fail(providers_module, monkeypatch):
    P = providers_module
    r = P.LocalRoseTTAFoldProvider(docker=True)
    monkeypatch.setattr(P.shutil, "which", lambda x: "/usr/bin/docker")
    def raise_exc(*a, **k):
        raise Exception("docker fail")
    monkeypatch.setattr(P.subprocess, "run", raise_exc)
    assert r.healthcheck() is False


def test_rosetta_predict_timeout_before_setup(providers_module, monkeypatch):
    P = providers_module
    r = P.LocalRoseTTAFoldProvider(docker=False)
    monkeypatch.setattr(P, "_time_left", lambda d: 0.0)
    with pytest.raises(P.PredictionError) as ei:
        r.predict("AAAA", timeout=0.0)
    assert ei.value.code == "TIMEOUT"


def test_rosetta_predict_subprocess_error(providers_module, monkeypatch, tmp_path):
    P = providers_module
    r = P.LocalRoseTTAFoldProvider(docker=False)
    def mock_run(*a, **k):
        return types.SimpleNamespace(returncode=1, stdout="out", stderr="err")
    monkeypatch.setattr(P.subprocess, "run", mock_run)
    with pytest.raises(P.PredictionError) as ei:
        r.predict("AAAA", timeout=10.0)
    assert ei.value.code == "REMOTE_ERROR"


def test_rosetta_predict_no_pdb_output(providers_module, monkeypatch, tmp_path):
    P = providers_module
    r = P.LocalRoseTTAFoldProvider(docker=False)
    def mock_run(*a, **k):
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(P.subprocess, "run", mock_run)
    monkeypatch.setattr(Path, "glob", lambda self, p: [])
    with pytest.raises(P.PredictionError) as ei:
        r.predict("AAAA", timeout=10.0)
    assert ei.value.code == "NO_OUTPUT"


def test_rosetta_predict_success(providers_module, monkeypatch, tmp_path):
    P = providers_module
    r = P.LocalRoseTTAFoldProvider(docker=False, executable="rf.py", weights_path="w.pt")
    def mock_run(*a, **k):
        return types.SimpleNamespace(returncode=0, stdout="ok", stderr="")
    def _glob(self, pat):
        if pat == "*.pdb":
            p = self / "x.pdb"
            p.write_text("PDB")
            return [p]
        return []
    monkeypatch.setattr(P.subprocess, "run", mock_run)
    monkeypatch.setattr(Path, "glob", _glob)
    out = r.predict("AAAA", timeout=10.0)
    assert out.provider == r.name and "PDB" in out.pdb_text


def test_rosetta_predict_docker_success(providers_module, monkeypatch, tmp_path):
    P = providers_module
    r = P.LocalRoseTTAFoldProvider(docker=True, weights_path=str(tmp_path / "w.pt"))
    monkeypatch.setattr(P.os.path, "dirname", lambda p: str(tmp_path))
    def mock_run(*a, **k):
        return types.SimpleNamespace(returncode=0, stdout="ok", stderr="")
    def _glob(self, pat):
        if pat == "*.pdb":
            p = self / "x.pdb"
            p.write_text("PDB")
            return [p]
        return []
    monkeypatch.setattr(P.subprocess, "run", mock_run)
    monkeypatch.setattr(Path, "glob", _glob)
    out = r.predict("AAAA", timeout=10.0)
    assert "PDB" in out.pdb_text


def test_rosetta_predict_timeout_subprocess(providers_module, monkeypatch):
    P = providers_module
    r = P.LocalRoseTTAFoldProvider(docker=False)
    def timeout_run(*a, **k):
        raise subprocess.TimeoutExpired("cmd", 1.0)
    monkeypatch.setattr(P.subprocess, "run", timeout_run)
    with pytest.raises(P.PredictionError) as ei:
        r.predict("A", timeout=1.0)
    assert ei.value.code == "TIMEOUT"


# APIColabFoldProvider

def test_colabfold_init(providers_module, monkeypatch):
    P = providers_module
    monkeypatch.setenv("COLABFOLD_TOKEN", "test_token")
    prov = P.APIColabFoldProvider()
    assert prov.name == "api_colabfold"
    assert "Bearer test_token" in prov.headers.get("Authorization", "")


def test_colabfold_healthcheck_success(providers_module, monkeypatch):
    P = providers_module
    prov = P.APIColabFoldProvider()
    def mock_get(*a, **k):
        return types.SimpleNamespace(status_code=200)
    monkeypatch.setattr(prov.session, "get", mock_get)
    assert prov.healthcheck() is True


def test_colabfold_healthcheck_fail(providers_module, monkeypatch):
    P = providers_module
    prov = P.APIColabFoldProvider()
    def mock_get(*a, **k):
        raise requests.RequestException("fail")
    monkeypatch.setattr(prov.session, "get", mock_get)
    assert prov.healthcheck() is False
