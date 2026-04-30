# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Advanced ingestion boundaries for proteomics exchange formats."""

from __future__ import annotations

from pathlib import Path

from defusedxml import ElementTree as ET
from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class MzIdentMlIngestionReport(JsonModel):
    """Structured mzIdentML ingestion support/refusal report."""

    model_config = ConfigDict(extra="forbid")

    supported: bool
    spectrum_identification_result_count: int = Field(..., ge=0)
    spectrum_identification_item_count: int = Field(..., ge=0)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)
    lost_fields: tuple[str, ...] = Field(default_factory=tuple)


def parse_mzidentml_or_refuse(path: Path) -> MzIdentMlIngestionReport:
    """Parse mzIdentML core identification surfaces or return precise refusal details."""
    root = ET.parse(path).getroot()
    tag = _local_name(root.tag)
    if tag != "MzIdentML":
        return MzIdentMlIngestionReport(
            supported=False,
            spectrum_identification_result_count=0,
            spectrum_identification_item_count=0,
            diagnostics=(
                "input root is not MzIdentML",
                "supported root tag: MzIdentML",
            ),
        )

    results = root.findall(".//{*}SpectrumIdentificationResult")
    items = root.findall(".//{*}SpectrumIdentificationItem")
    if not results:
        return MzIdentMlIngestionReport(
            supported=False,
            spectrum_identification_result_count=0,
            spectrum_identification_item_count=0,
            diagnostics=(
                "missing SpectrumIdentificationResult entries",
                "file cannot be normalized into core PSM contracts without identification results",
            ),
        )

    lost_fields: list[str] = []
    if root.find(".//{*}ProteinDetectionList") is None:
        lost_fields.append("protein_detection_list")
    if root.find(".//{*}FragmentationTable") is None:
        lost_fields.append("fragmentation_table")

    return MzIdentMlIngestionReport(
        supported=True,
        spectrum_identification_result_count=len(results),
        spectrum_identification_item_count=len(items),
        diagnostics=(
            "parsed mzIdentML identification results",
            "normalization keeps explicit counts for result and item surfaces",
        ),
        lost_fields=tuple(lost_fields),
    )


def _local_name(tag: str) -> str:
    if "}" not in tag:
        return tag
    return tag.rsplit("}", 1)[1]
