# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Private test-support helpers for structured public function docstring audits."""

from __future__ import annotations

import inspect
from dataclasses import dataclass

REQUIRED_PUBLIC_FUNCTION_DOCSTRING_SECTIONS = (
    "Inputs:",
    "Outputs:",
    "Failure Modes:",
    "Scientific Caveats:",
)


@dataclass(frozen=True)
class PublicFunctionDocstringObservation:
    """Observed structured docstring state for one public function."""

    qualified_name: str
    missing_sections: tuple[str, ...]
    empty_sections: tuple[str, ...]
    out_of_order_sections: tuple[str, ...]


@dataclass(frozen=True)
class PublicFunctionDocstringReport:
    """Structured report over a curated set of public function docstrings."""

    function_count: int
    compliant_qualified_names: tuple[str, ...]
    violating_observations: tuple[PublicFunctionDocstringObservation, ...]


def build_public_function_docstring_report(
    functions: tuple[object, ...],
) -> PublicFunctionDocstringReport:
    """Audit public functions for the required structured docstring sections."""

    compliant_qualified_names: list[str] = []
    violating_observations: list[PublicFunctionDocstringObservation] = []
    for function in functions:
        qualified_name = _qualified_name(function)
        docstring = inspect.getdoc(function) or ""
        sections, section_order = _extract_sections(docstring)
        missing_sections = tuple(
            section
            for section in REQUIRED_PUBLIC_FUNCTION_DOCSTRING_SECTIONS
            if section not in sections
        )
        empty_sections = tuple(
            section
            for section in REQUIRED_PUBLIC_FUNCTION_DOCSTRING_SECTIONS
            if section in sections and not sections[section].strip()
        )
        present_required_sections = tuple(
            section
            for section in section_order
            if section in REQUIRED_PUBLIC_FUNCTION_DOCSTRING_SECTIONS
        )
        out_of_order_sections = (
            ()
            if present_required_sections
            == tuple(
                section
                for section in REQUIRED_PUBLIC_FUNCTION_DOCSTRING_SECTIONS
                if section in sections
            )
            else present_required_sections
        )
        observation = PublicFunctionDocstringObservation(
            qualified_name=qualified_name,
            missing_sections=missing_sections,
            empty_sections=empty_sections,
            out_of_order_sections=out_of_order_sections,
        )
        if (
            not observation.missing_sections
            and not observation.empty_sections
            and not observation.out_of_order_sections
        ):
            compliant_qualified_names.append(qualified_name)
            continue
        violating_observations.append(observation)
    return PublicFunctionDocstringReport(
        function_count=len(functions),
        compliant_qualified_names=tuple(compliant_qualified_names),
        violating_observations=tuple(violating_observations),
    )


def _extract_sections(docstring: str) -> tuple[dict[str, str], tuple[str, ...]]:
    sections: dict[str, str] = {}
    section_order: list[str] = []
    current_section: str | None = None
    current_lines: list[str] = []
    for line in docstring.splitlines():
        stripped = line.strip()
        matched_header = next(
            (
                header
                for header in REQUIRED_PUBLIC_FUNCTION_DOCSTRING_SECTIONS
                if stripped == header or stripped.startswith(f"{header} ")
            ),
            None,
        )
        if matched_header is not None:
            if current_section is not None:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = matched_header
            section_order.append(matched_header)
            trailing_content = stripped[len(matched_header) :].strip()
            current_lines = [trailing_content] if trailing_content else []
            continue
        if current_section is not None:
            current_lines.append(stripped)
    if current_section is not None:
        sections[current_section] = "\n".join(current_lines).strip()
    return sections, tuple(section_order)


def _qualified_name(function: object) -> str:
    module_name = getattr(function, "__module__", "")
    qualname = getattr(function, "__qualname__", repr(function))
    return f"{module_name}.{qualname}" if module_name else str(qualname)


__all__ = [
    "PublicFunctionDocstringObservation",
    "PublicFunctionDocstringReport",
    "REQUIRED_PUBLIC_FUNCTION_DOCSTRING_SECTIONS",
    "build_public_function_docstring_report",
]
