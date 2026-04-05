# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Report rendering and serialization helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
import json
import os
from typing import Any

import numpy as np

from agentic_proteins.report.compute import (
    SS8,
    Metrics,
    PLDDTBand,
    PrimarySummary,
    SecondarySummary,
    TertiarySummary,
    json_safe,
)
from agentic_proteins.report.model import Report

try:
    from langchain_community.llms import HuggingFaceHub
    from langchain_core.prompts import PromptTemplate

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


def from_json(s: str) -> Report:
    """from_json."""
    data = json.loads(s)
    if data.get("schema_version", "0.0") != "1.0":
        raise ValueError("Unsupported schema version")
    bands = data["metrics"]["tertiary"]["plddt_bands"]
    if set(bands.keys()) != {b.value for b in PLDDTBand}:
        raise ValueError("Invalid pLDDT band keys")
    for v in bands.values():
        if not (0.0 <= v <= 100.0):
            raise ValueError("pLDDT band out of [0,100]")
    ss8 = data["metrics"]["secondary"]["ss8_pct"]
    if set(ss8.keys()) - {s.value for s in SS8}:
        raise ValueError("Invalid SS8 keys")

    return Report(
        provider=data["provider"],
        metrics=Metrics(
            primary=PrimarySummary(**data["metrics"]["primary"]),
            secondary=SecondarySummary(**data["metrics"]["secondary"]),
            tertiary=TertiarySummary(**data["metrics"]["tertiary"]),
            ref_residues=data["metrics"].get("ref_residues"),
            n_matched_pairs=data["metrics"].get("n_matched_pairs"),
            seq_identity=data["metrics"].get("seq_identity"),
            gap_fraction=data["metrics"].get("gap_fraction"),
        ),
        notes=data["notes"],
        low_conf_segments=tuple(
            tuple(seg) for seg in data.get("low_conf_segments", [])
        ),
        warnings=data.get("warnings", []),
        links=data.get("links", {}),
        schema_version=data.get("schema_version", "1.0"),
        provenance=data.get("provenance", {}),
    )


def json_schema() -> dict[str, Any]:
    """json_schema."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "schema_version": {"type": "string", "const": "1.0"},
            "provenance": {"type": "object"},
            "provider": {"type": "string"},
            "metrics": {
                "type": "object",
                "properties": {
                    "primary": {
                        "type": "object",
                        "properties": {
                            "length": {"type": "integer", "minimum": 1},
                            "aa_composition": {"type": "object"},
                            "gravy": {"type": ["number", "null"]},
                            "pI": {"type": ["number", "null"]},
                            "pct_disorder": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "pct_low_complexity": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "has_signal_peptide": {"type": ["boolean", "null"]},
                            "has_tm_segments": {"type": ["boolean", "null"]},
                        },
                        "required": ["length"],
                    },
                    "secondary": {
                        "type": "object",
                        "properties": {
                            "pct_helix": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "pct_sheet": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "pct_coil": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "ss8_pct": {"type": "object"},
                            "q3": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "q8": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "sov99": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": ["pct_helix", "pct_sheet", "pct_coil"],
                    },
                    "tertiary": {
                        "type": "object",
                        "properties": {
                            "mean_plddt": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "plddt_bands": {"type": "object"},
                            "pae_median": {"type": ["number", "null"]},
                            "pae_q90": {"type": ["number", "null"]},
                            "rg": {"type": ["number", "null"]},
                            "sasa": {"type": ["number", "null"]},
                            "hbonds": {"type": ["integer", "null"]},
                            "rama_outliers_pct": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "clashscore": {"type": ["number", "null"]},
                            "rmsd": {"type": ["number", "null"]},
                            "gdt_ts": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "gdt_ha": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "tm_score": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "lddt": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "n_interfaces": {"type": ["integer", "null"]},
                            "buried_sasa": {"type": ["number", "null"]},
                            "irmsd": {"type": ["number", "null"]},
                            "dockq": {
                                "type": ["number", "null"],
                                "minimum": 0,
                                "maximum": 1,
                            },
                        },
                        "required": ["mean_plddt"],
                    },
                    "ref_residues": {"type": ["integer", "null"]},
                    "n_matched_pairs": {"type": ["integer", "null"]},
                    "seq_identity": {
                        "type": ["number", "null"],
                        "minimum": 0,
                        "maximum": 1,
                    },
                    "gap_fraction": {
                        "type": ["number", "null"],
                        "minimum": 0,
                        "maximum": 1,
                    },
                },
                "required": ["primary", "secondary", "tertiary"],
            },
            "notes": {"type": "string"},
            "low_conf_segments": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2,
                },
            },
            "warnings": {"type": "array", "items": {"type": "string"}},
            "links": {"type": "object"},
        },
        "required": ["provider", "metrics", "notes"],
    }


def to_json(report: Report, pretty: bool = True, compact: bool = False) -> str:
    """to_json."""
    payload = json_safe(asdict(report))
    indent = 2 if pretty else None
    separators = (",", ":") if compact else None
    return json.dumps(
        payload,
        indent=indent,
        separators=separators,
        ensure_ascii=False,
        sort_keys=True,
    )


def to_text(report: Report) -> str:
    """to_text."""
    m = report.metrics
    lines = [
        f"Provider: {report.provider}",
        "Primary Structure:",
        f"  Length: {m.primary.length}",
        f"  GRAVY: {format_value(m.primary.gravy, '{:.2f}')}",
        f"  pI: {format_value(m.primary.pI, '{:.2f}')}",
        f"  Disorder: {format_pct(m.primary.pct_disorder / 100 if m.primary.pct_disorder is not None else None)}",
        f"  Low Complexity: {format_pct(m.primary.pct_low_complexity / 100 if m.primary.pct_low_complexity is not None else None)}",
        f"  Signal Peptide: {'Yes' if m.primary.has_signal_peptide else 'No' if m.primary.has_signal_peptide is not None else 'n/a'}",
        f"  TM Segments: {'Yes' if m.primary.has_tm_segments else 'No' if m.primary.has_tm_segments is not None else 'n/a'}",
        "Secondary Structure:",
        f"  Helix: {format_pct(m.secondary.pct_helix / 100):>6s} | Sheet: {format_pct(m.secondary.pct_sheet / 100):>6s} | Coil: {format_pct(m.secondary.pct_coil / 100):>6s}",
    ]
    if m.secondary.ss8_pct:
        ordered_ss8 = [SS8.H, SS8.E, SS8.G, SS8.I, SS8.B, SS8.T, SS8.S, SS8.C]
        ss8_str = ", ".join(
            f"{s.value}: {format_pct(m.secondary.ss8_pct.get(s, 0.0) / 100):>5s}"
            for s in ordered_ss8
            if m.secondary.ss8_pct.get(s, 0.0) > 0
        )
        lines.append(f"  SS8: {ss8_str}")
    if m.secondary.q3 is not None:
        lines.append(f"  Q3 Accuracy: {format_value(m.secondary.q3, '{:.1f}')}%")
    lines += [
        "Tertiary Structure:",
        f"  Proxy mean pLDDT (CA): {format_value(m.tertiary.mean_plddt, '{:.1f}')}",
        f"  pAE Median: {format_value(m.tertiary.pae_median, '{:.1f}')}",
        f"  Rg (Å): {format_value(m.tertiary.rg, '{:.2f}')}",
        f"  SASA (Å²): {format_value(m.tertiary.sasa, '{:.0f}')}",
        f"  H-bonds: {m.tertiary.hbonds if m.tertiary.hbonds is not None else 'n/a'}",
        f"  Rama Outliers: {format_pct(m.tertiary.rama_outliers_pct / 100 if m.tertiary.rama_outliers_pct is not None else None)}",
        f"  Clashscore: {format_value(m.tertiary.clashscore, '{:.2f}')}",
    ]
    if m.tertiary.rmsd is not None:
        cov_pred_str = f"{m.cov_pred:.0f}%" if m.cov_pred is not None else "n/a"
        cov_ref_str = f"{m.cov_ref:.0f}%" if m.cov_ref is not None else "n/a"
        lines.extend(
            [
                "Comparison Metrics:",
                f"  RMSD (CA, Å): {format_value(m.tertiary.rmsd, '{:.2f}')} ({cov_pred_str} cov pred / {cov_ref_str} cov ref)",
                f"  GDT-TS: {format_value(m.tertiary.gdt_ts, '{:.1f}')} | GDT-HA: {format_value(m.tertiary.gdt_ha, '{:.1f}')}",
                f"  TM-score: {format_value(m.tertiary.tm_score, '{:.3f}')}",
                f"  lDDT: {format_value(m.tertiary.lddt, '{:.2f}')}",
                f"  Seq ID: {format_pct(m.seq_identity)}",
                f"  Gap frac: {format_pct(m.gap_fraction)}",
            ]
        )
    if m.tertiary.n_interfaces is not None:
        lines.extend(
            [
                "Interfaces:",
                f"  Count: {m.tertiary.n_interfaces}",
                f"  Buried SASA (Å²): {format_value(m.tertiary.buried_sasa, '{:.0f}')}",
                f"  iRMSD (Å): {format_value(m.tertiary.irmsd, '{:.2f}')}",
                f"  DockQ: {format_value(m.tertiary.dockq, '{:.3f}')}",
            ]
        )
    if report.links:
        lines.append("Links:")
        for k, v in sorted(report.links.items()):
            lines.append(f"  {k}: {v}")
    if report.warnings:
        lines.append("Warnings:")
        for w in report.warnings:
            lines.append(f"  - {w}")
    lines.extend(
        [
            f"Notes: {report.notes}",
            "",
            "Confidence Summary:",
            confidence_summary(report),
        ]
    )
    if report.low_conf_segments:
        seg_str = ", ".join(f"{s}-{e}" for s, e in report.low_conf_segments)
        lines.append(
            "Low-confidence segments (<70 pLDDT, ≥8 res): "
            f"{len(report.low_conf_segments)} ({seg_str})"
        )
    return "\n".join(lines)


def confidence_summary(report: Report) -> str:
    """confidence_summary."""
    mean_p = report.metrics.tertiary.mean_plddt
    if np.isnan(mean_p):
        return "No confidence data available."
    ordered_bands = sorted(
        report.metrics.tertiary.plddt_bands.items(),
        key=lambda kv: list(PLDDTBand).index(kv[0]),
    )
    dist_str = ", ".join(f"{k.value}: {v:.0f}%" for k, v in ordered_bands)
    segs_str = (
        "low-confidence segments: "
        + ", ".join(f"{s}-{e}" for s, e in report.low_conf_segments)
        if report.low_conf_segments
        else "no notable low-confidence segments"
    )
    if mean_p >= 90:
        return f"High confidence overall ({dist_str}); {segs_str}."
    if mean_p >= 70:
        return f"Confident core ({dist_str}); check {segs_str}."
    if mean_p >= 50:
        return f"Low-confidence ({dist_str}); refine loops in {segs_str}."
    return f"Unreliable ({dist_str}); validate experimentally, especially {segs_str}."


def nl_summary(report: Report, generator: Callable | None = None) -> str:
    """nl_summary."""
    if generator:
        try:
            return generator(report)
        except Exception as exc:  # noqa: BLE001
            return f"NL summary failed: {str(exc)}"
    api_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not api_token:
        return "NL summary unavailable: HF_TOKEN or HUGGINGFACEHUB_API_TOKEN not set."
    if not LANGCHAIN_AVAILABLE:
        return "NL summary unavailable: LangChain dependencies not installed or import failed."

    repo = os.getenv("HF_REPO_ID", "google/flan-t5-large")
    temp = float(os.getenv("HF_TEMPERATURE", "0.1"))
    max_new = int(os.getenv("HF_MAX_NEW_TOKENS", "256"))

    llm = HuggingFaceHub(
        repo_id=repo,
        huggingfacehub_api_token=api_token,
        model_kwargs={
            "task": "text2text-generation",
            "temperature": temp,
            "max_new_tokens": max_new,
        },
    )

    template = """
    Summarize for non-experts:
    Provider: {provider}
    Metrics: {metrics}
    Low-confidence: {low}
    Notes: {notes}
    ---\nSummary:
    """
    prompt = PromptTemplate.from_template(template)
    inputs = {
        "provider": report.provider,
        "metrics": json.dumps(json_safe(asdict(report.metrics)), ensure_ascii=False),
        "low": str(report.low_conf_segments),
        "notes": report.notes,
    }

    try:
        formatted = prompt.format(**inputs)
        return llm(formatted)
    except Exception:
        return "NL summary unavailable."


def format_value(v: float | None, fmt: str) -> str:
    """format_value."""
    if v is None:
        return "n/a"
    vf = float(v)
    return "n/a" if np.isnan(vf) or np.isinf(vf) else fmt.format(vf)


def format_pct(v: float | None) -> str:
    """format_pct."""
    if v is None:
        return "n/a"
    vf = float(v)
    return "n/a" if np.isnan(vf) or np.isinf(vf) else f"{vf * 100:.1f}%"
