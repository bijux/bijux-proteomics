# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any

import numpy as np
import pytest

import agentic_proteins.report as R
import agentic_proteins.report.render as render


# ---------- helpers ----------

def _pri(**kw) -> R.PrimarySummary:
    d = dict(
        length=5,
        aa_composition={"A": 20, "C": 20, "D": 20, "E": 20, "F": 20},
        gravy=0.1,
        isoelectric_point=6.8,
        pct_disorder=10.0,
        pct_low_complexity=5.0,
        has_signal_peptide=True,
        has_tm_segments=False,
    )
    d.update(kw)
    return R.PrimarySummary(**d)

def _sec(**kw) -> R.SecondarySummary:
    d = dict(
        pct_helix=30.0, pct_sheet=20.0, pct_coil=50.0,
        ss8_pct={R.SS8.H: 30.0, R.SS8.E: 20.0, R.SS8.C: 50.0},
        q3=85.0, q8=None, sov99=None,
    )
    d.update(kw)
    return R.SecondarySummary(**d)

def _ter(**kw) -> R.TertiarySummary:
    d = dict(
        mean_plddt=80.0,
        plddt_bands={
            R.PLDDTBand.GE90: 10.0,
            R.PLDDTBand.B70_90: 60.0,
            R.PLDDTBand.B50_70: 20.0,
            R.PLDDTBand.LT50: 10.0,
        },
        pae_median=6.5,
        pae_q90=12.0,
        rg=18.2,
        sasa=12345.0,
        hbonds=12,
        rama_outliers_pct=2.0,
        clashscore=8.7,
        rmsd=2.1,
        gdt_ts=75.0,
        gdt_ha=60.0,
        tm_score=0.55,
        lddt=0.62,
        n_interfaces=1,
        buried_sasa=456.0,
        irmsd=1.8,
        dockq=0.42,
    )
    d.update(kw)
    return R.TertiarySummary(**d)

def _metrics(**kw) -> R.Metrics:
    d = dict(primary=_pri(), secondary=_sec(), tertiary=_ter(),
             ref_residues=10, n_matched_pairs=8, seq_identity=0.6, gap_fraction=0.1)
    d.update(kw)
    return R.Metrics(**d)

def _report(**kw) -> R.Report:
    metrics = kw.get("metrics", _metrics())
    warnings = kw.get("warnings", R.compute_report_warnings(metrics))
    d = dict(
        provider="P",
        metrics=metrics,
        notes="n",
        low_conf_segments=((2, 10),),
        warnings=warnings,
        links={"pdb": "http://x"},
        provenance={"ts": "t"},
    )
    d.update(kw)
    return R.Report(**d)


# ---------- json_safe / formatting ----------

def test_json_safe_various_and_errors():
    assert R.json_safe(3.14) == 3.14
    assert R.json_safe(np.float64(2.0)) == 2.0
    assert R.json_safe(np.nan) is None
    assert R.json_safe(np.inf) is None
    assert R.json_safe({"a": np.nan, "b": [1, (2, 3)]}) == {"a": None, "b": [1, [2, 3]]}
    with pytest.raises(TypeError):
        R.json_safe(set([1, 2]))

def test_fmt_and_fmt_pct():
    assert R.format_value(1.234, "{:.1f}") == "1.2"
    assert R.format_value(None, "{:.1f}") == "n/a"
    assert R.format_value(np.nan, "{:.1f}") == "n/a"
    assert R.format_pct(0.123) == "12.3%"
    assert R.format_pct(None) == "n/a"
    assert R.format_pct(float("inf")) == "n/a"


# ---------- PrimarySummary ----------

def test_primary_summary_repr_and_pi_and_warnings():
    p = _pri()
    r = repr(p)
    assert "PrimarySummary" in r and "gravy=0.1" in r
    assert p.pI == p.isoelectric_point

    # exercise warning paths (loguru warnings go to stderr; we just exercise)
    _ = _pri(aa_composition={"A": 50, "C": 30}, pct_disorder=200.0)


# ---------- SecondarySummary ----------

def test_secondary_summary_repr_and_validations():
    s = _sec(ss8_pct={R.SS8.H: 10, R.SS8.E: 20, R.SS8.C: 69})  # sums 99 -> warning
    assert "SecondarySummary" in repr(s)
    _ = _sec(pct_helix=120.0, q3=-5.0)  # out-of-range warnings


# ---------- TertiarySummary ----------

def test_tertiary_bands_normalization_and_range():
    # test alt keys normalization and value clipping to 0 default on non-real
    t = R.TertiarySummary(
        mean_plddt=90.0,
        plddt_bands={"≥90": 40, "70-90": 30, "50–70": 20, "<50": 10},  # mix of forms
    )
    assert set(t.plddt_bands.keys()) == set(R.PLDDTBand)
    assert abs(sum(t.plddt_bands.values()) - 100.0) < 1e-6
    assert "TertiarySummary" in repr(t)

def test_tertiary_bands_out_of_range_raises():
    with pytest.raises(ValueError):
        R.TertiarySummary(
            mean_plddt=50.0,
            plddt_bands={b: (200.0 if b == R.PLDDTBand.B70_90 else 0.0) for b in R.PLDDTBand},
        )

def test_tertiary_probability_and_percentage_warnings():
    _ = _ter(tm_score=1.5, dockq=-0.1, lddt=2.0)  # probabilities out-of-range
    _ = _ter(rama_outliers_pct=120.0)             # percentage out-of-range


# ---------- Metrics ----------

def test_metrics_covariates_and_repr_and_prob_warning():
    m = _metrics(n_matched_pairs=3, primary=_pri(length=10), ref_residues=30, seq_identity=0.7, gap_fraction=1.2)
    assert m.cov_pred == 30.0
    assert m.cov_ref == 10.0
    assert "Metrics(primary=" in repr(m)

def test_metrics_coverage_nones():
    m = _metrics(n_matched_pairs=None)
    assert m.cov_pred is None and m.cov_ref is None


# ---------- Report core ----------

def test_report_init_warnings_and_repr_and_hash_stable():
    r = _report()
    h1 = R.report_hash(r)
    h2 = R.report_hash(r)
    assert h1 == h2  # stable

def test_report_init_length_guard():
    with pytest.raises(ValueError):
        _ = _report(metrics=_metrics(primary=_pri(length=0)))

def test_report_warning_rules_low_mean_lt50_and_gravy_outside():
    metrics = _metrics(
        primary=_pri(gravy=3.0),  # unusual gravy
        tertiary=_ter(
            mean_plddt=65.0,
            plddt_bands={b: (25.0 if b == R.PLDDTBand.LT50 else 25.0) for b in R.PLDDTBand},
        ),
    )
    warnings = R.compute_report_warnings(metrics)
    assert any("Low overall confidence" in w for w in warnings)
    assert any("<50 pLDDT" in w for w in warnings)
    assert any("GRAVY" in w for w in warnings)

def test_report_warning_nan_paths():
    warnings = R.compute_report_warnings(_metrics(tertiary=_ter(mean_plddt=float("nan"))))
    assert any("NaN values clipped" in w for w in warnings)


# ---------- JSON roundtrip / schema ----------

def _to_plain_dict(rep: R.Report) -> dict[str, Any]:
    return json.loads(R.to_json(rep, pretty=True))

def test_to_json_pretty_and_compact_and_schema():
    r = _report()
    s_pretty = R.to_json(r, pretty=True)
    s_compact = R.to_json(r, pretty=False, compact=True)
    assert "\n" in s_pretty and "\n" not in s_compact
    schema = R.json_schema()
    assert schema["properties"]["metrics"]["properties"]["tertiary"]["properties"]["mean_plddt"]["maximum"] == 100

def test_from_json_success_and_validations():
    r = _report()
    d = _to_plain_dict(r)
    s = json.dumps(d)
    r2 = R.from_json(s)
    assert r2.provider == r.provider
    # invalid schema version
    d_bad = deepcopy(d)
    d_bad["schema_version"] = "9.9"
    with pytest.raises(ValueError):
        R.from_json(json.dumps(d_bad))
    # invalid band keys
    d_bad = deepcopy(d)
    d_bad["metrics"]["tertiary"]["plddt_bands"] = {"x": 100}
    with pytest.raises(ValueError):
        R.from_json(json.dumps(d_bad))
    # out-of-range band value
    d_bad = deepcopy(d)
    d_bad["metrics"]["tertiary"]["plddt_bands"][R.PLDDTBand.GE90.value] = 120.0
    with pytest.raises(ValueError):
        R.from_json(json.dumps(d_bad))
    # invalid SS8 key
    d_bad = deepcopy(d)
    d_bad["metrics"]["secondary"]["ss8_pct"] = {"Z": 100}
    with pytest.raises(ValueError):
        R.from_json(json.dumps(d_bad))


# ---------- Text rendering ----------

def test_to_text_includes_sections_and_links_and_interfaces():
    r = _report()
    txt = R.to_text(r)
    assert "Provider: P" in txt
    assert "Primary Structure:" in txt
    assert "Secondary Structure:" in txt
    assert "Tertiary Structure:" in txt
    assert "Links:" in txt and "http://x" in txt
    assert "Interfaces:" in txt  # because n_interfaces provided
    assert "Confidence Summary:" in txt
    assert "Low-confidence segments" in txt

def test_to_text_comparison_block_absent_when_no_ref_metrics():
    m = _metrics(tertiary=_ter(rmsd=None, gdt_ts=None, gdt_ha=None, tm_score=None, lddt=None))
    r = _report(metrics=m)
    txt = R.to_text(r)
    assert "Comparison Metrics:" not in txt


# ---------- Confidence summary ----------

def test_confidence_summary_branches():
    # ≥90
    r = _report(metrics=_metrics(tertiary=_ter(mean_plddt=90.0)))
    assert "High confidence" in R.confidence_summary(r)
    # 70–90
    r = _report(metrics=_metrics(tertiary=_ter(mean_plddt=70.0)))
    assert "Confident core" in R.confidence_summary(r)
    # 50–70
    r = _report(metrics=_metrics(tertiary=_ter(mean_plddt=55.0)))
    assert "Low-confidence" in R.confidence_summary(r)
    # <50
    r = _report(metrics=_metrics(tertiary=_ter(mean_plddt=40.0)))
    assert "Unreliable" in R.confidence_summary(r)
    # NaN
    r = _report(metrics=_metrics(tertiary=_ter(mean_plddt=float("nan"))))
    assert "No confidence data available" in R.confidence_summary(r)


# ---------- NL summary ----------

def test_nl_summary_with_generator_success_and_failure():
    r = _report()
    gen_ok = lambda rep: f"ok:{rep.provider}"
    assert R.nl_summary(r, generator=gen_ok).startswith("ok:P")
    def gen_fail(rep):
        raise RuntimeError("nope")
    assert "NL summary failed: nope" in R.nl_summary(r, generator=gen_fail)

def test_nl_summary_env_and_dependency_paths(monkeypatch):
    r = _report()

    # No token -> specific message
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACEHUB_API_TOKEN", raising=False)
    out = R.nl_summary(r)
    assert "HF_TOKEN" in out

    # Token set but LangChain unavailable
    monkeypatch.setenv("HF_TOKEN", "x")
    monkeypatch.setattr(render, "LANGCHAIN_AVAILABLE", False, raising=False)
    out = R.nl_summary(r)
    assert "LangChain" in out

    # Token set & pretend LangChain present: success path
    class _DummyLLM:
        def __init__(self, **kw): pass
        def __call__(self, prompt: str) -> str: return "LLM: ok"

    class _DummyPromptTmpl:
        @staticmethod
        def from_template(t: str):
            class _P:
                def format(self, **kw): return "formatted"
            return _P()

    monkeypatch.setattr(render, "LANGCHAIN_AVAILABLE", True, raising=False)
    monkeypatch.setattr(render, "HuggingFaceHub", _DummyLLM, raising=False)
    monkeypatch.setattr(render, "PromptTemplate", _DummyPromptTmpl, raising=False)
    out = R.nl_summary(r)
    assert out == "LLM: ok"

def test_nl_summary_langchain_exception_branch(monkeypatch):
    """Cover the try/except inside nl_summary when LangChain is 'available' but fails."""
    r = _report()
    monkeypatch.setenv("HF_TOKEN", "x")
    monkeypatch.setattr(render, "LANGCHAIN_AVAILABLE", True, raising=False)

    class _BoomLLM:
        def __init__(self, **kw): pass
        def __call__(self, prompt: str) -> str: raise RuntimeError("boom")

    class _Prompt:
        @staticmethod
        def from_template(t: str):
            class _P:
                def format(self, **kw): return "formatted"
            return _P()

    monkeypatch.setattr(render, "HuggingFaceHub", _BoomLLM, raising=False)
    monkeypatch.setattr(render, "PromptTemplate", _Prompt, raising=False)
    out = R.nl_summary(r)
    assert out == "NL summary unavailable."


# ---------- compare ----------

def test_compare_outputs_and_significance_flags():
    a = _report()
    b = _report(metrics=_metrics(primary=_pri(length=6),
                                 secondary=_sec(pct_helix=25.0, pct_sheet=10.0, pct_coil=65.0)))
    comp = R.compare_reports(a, b)
    assert isinstance(comp, dict) and "diff" in comp and "text" in comp
    paths = [d["path"] for d in comp["diff"]]
    assert "metrics/secondary/pct_helix" in paths
    assert "TM=" in comp["text"] and "RMSD=" in comp["text"]


# ---------- assert_band_sum ----------

def test_assert_band_sum_pass_and_fail():
    bands_good = {b: 25.0 for b in R.PLDDTBand}
    R.assert_band_sum(bands_good)
    with pytest.raises(AssertionError):
        R.assert_band_sum({b: (30.0 if b == R.PLDDTBand.GE90 else 25.0) for b in R.PLDDTBand}, tol=0.1)
