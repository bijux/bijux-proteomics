# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_proteins.providers.errors import PredictionError
from agentic_proteins.providers.local.esmfold import LocalESMFoldProvider


torch = pytest.importorskip("torch")


def test_format_atom_name_alignment() -> None:
    assert LocalESMFoldProvider._format_atom_name("CA", "C") == "  CA"
    assert LocalESMFoldProvider._format_atom_name("ATOM", "CA") == "ATOM"


def test_positions_to_backbone_pdb_smoke() -> None:
    provider = LocalESMFoldProvider.__new__(LocalESMFoldProvider)
    sequence = "AC"
    positions = torch.zeros((2, 4, 3))
    positions[0, 0] = torch.tensor([1.0, 2.0, 3.0])
    positions[1, 1] = torch.tensor([4.0, 5.0, 6.0])
    plddt = torch.tensor([0.5, 0.9])
    pdb = provider._positions_to_backbone_pdb(sequence, positions, plddt)
    assert "ATOM" in pdb
    assert "ENDMDL" in pdb


def test_positions_to_backbone_pdb_invalid_shape() -> None:
    provider = LocalESMFoldProvider.__new__(LocalESMFoldProvider)
    sequence = "AC"
    positions = torch.zeros((1, 4, 3))
    plddt = torch.tensor([0.5, 0.9])
    with pytest.raises(PredictionError, match="Expected positions"):
        provider._positions_to_backbone_pdb(sequence, positions, plddt)


def test_positions_to_backbone_pdb_requires_atoms() -> None:
    provider = LocalESMFoldProvider.__new__(LocalESMFoldProvider)
    sequence = "AC"
    positions = torch.zeros((2, 3, 3))
    plddt = torch.tensor([0.5, 0.9])
    with pytest.raises(PredictionError, match="Need at least 4 atoms"):
        provider._positions_to_backbone_pdb(sequence, positions, plddt)


def test_positions_to_backbone_pdb_skips_nonfinite() -> None:
    provider = LocalESMFoldProvider.__new__(LocalESMFoldProvider)
    sequence = "AC"
    positions = torch.zeros((2, 4, 3))
    positions[0, 0] = torch.tensor([float("nan"), 0.0, 0.0])
    plddt = torch.tensor([0.5, 0.9])
    pdb = provider._positions_to_backbone_pdb(sequence, positions, plddt)
    assert "ENDMDL" in pdb


def test_to_per_res_plddt_normalizes_values() -> None:
    provider = LocalESMFoldProvider.__new__(LocalESMFoldProvider)
    raw = torch.tensor([[50.0, 60.0], [70.0, 80.0]])
    per_res = provider._to_per_res_plddt(raw, n_res=2, n_atoms=2)
    assert per_res.shape[0] == 2
    assert float(per_res.max().item()) <= 1.0


def test_to_per_res_plddt_rejects_bad_shape() -> None:
    provider = LocalESMFoldProvider.__new__(LocalESMFoldProvider)
    raw = torch.zeros((3,))
    with pytest.raises(PredictionError, match="Unexpected 1D pLDDT"):
        provider._to_per_res_plddt(raw, n_res=2, n_atoms=2)


def test_to_per_res_plddt_requires_dims() -> None:
    provider = LocalESMFoldProvider.__new__(LocalESMFoldProvider)
    raw = torch.zeros((2, 2))
    with pytest.raises(TypeError, match="n_res"):
        provider._to_per_res_plddt(raw)


def test_to_per_res_plddt_handles_5d() -> None:
    provider = LocalESMFoldProvider.__new__(LocalESMFoldProvider)
    raw = torch.ones((2, 1, 2, 4, 1))
    per_res = provider._to_per_res_plddt(raw, n_res=2, n_atoms=4)
    assert per_res.shape == (2,)


def test_to_per_res_plddt_handles_3d() -> None:
    provider = LocalESMFoldProvider.__new__(LocalESMFoldProvider)
    raw = torch.ones((2, 4, 1))
    per_res = provider._to_per_res_plddt(raw, n_res=2, n_atoms=4)
    assert per_res.shape == (2,)


def test_predict_empty_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = LocalESMFoldProvider(model_path="models/esmfold", token=None)
    monkeypatch.setattr(provider, "_check_circuit", lambda: None)
    with pytest.raises(PredictionError, match="Empty sequence"):
        provider.predict("", timeout=1.0)


def test_predict_missing_outputs(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = LocalESMFoldProvider(model_path="models/esmfold", token=None)
    monkeypatch.setattr(provider, "_check_circuit", lambda: None)

    class _Inputs:
        def to(self, _device: str) -> dict[str, torch.Tensor]:
            return {"input_ids": torch.ones((1, 1))}

    class _Tokenizer:
        def __call__(self, *_args, **_kwargs) -> _Inputs:
            return _Inputs()

    class _Model:
        def __call__(self, **_kwargs):
            return type("Out", (), {"positions": None, "plddt": None})()

    def _load_model() -> None:
        provider.tokenizer = _Tokenizer()
        provider.model = _Model()

    monkeypatch.setattr(provider, "_load_model", _load_model)
    with pytest.raises(PredictionError, match="missing 'positions'"):
        provider.predict("ACD", timeout=1.0)


def test_predict_success_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = LocalESMFoldProvider(model_path="models/esmfold", token=None)
    provider.device = "cpu"
    monkeypatch.setattr(provider, "_check_circuit", lambda: None)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    class _Inputs:
        def to(self, _device: str) -> dict[str, torch.Tensor]:
            return {"input_ids": torch.ones((1, 3))}

    class _Tokenizer:
        def __call__(self, *_args, **_kwargs) -> _Inputs:
            return _Inputs()

    class _Model:
        def __call__(self, **_kwargs):
            positions = torch.zeros((3, 4, 3))
            plddt = torch.ones((3, 4))
            return type("Out", (), {"positions": positions, "plddt": plddt})()

    def _load_model() -> None:
        provider.tokenizer = _Tokenizer()
        provider.model = _Model()

    monkeypatch.setattr(provider, "_load_model", _load_model)
    result = provider.predict("ACD", timeout=2.0, seed=123)
    assert result.pdb_text
    assert result.raw["sequence_length"] == 3
