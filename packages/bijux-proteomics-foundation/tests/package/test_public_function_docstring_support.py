# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation.testing.public_function_docstrings import (
    build_public_function_docstring_report,
)


def test_public_function_docstring_report_accepts_structured_docstrings() -> None:
    def compliant_function() -> None:
        """Summarize one stable public function.

        Inputs:
        The function accepts no public inputs.

        Outputs:
        The function returns ``None``.

        Failure Modes:
        The function raises no governed public exceptions.

        Scientific Caveats:
        The function does not perform scientific interpretation.
        """

    report = build_public_function_docstring_report((compliant_function,))

    assert report.function_count == 1
    assert report.compliant_qualified_names == (
        f"{__name__}.test_public_function_docstring_report_accepts_structured_docstrings.<locals>.compliant_function",
    )
    assert report.violating_observations == ()


def test_public_function_docstring_report_flags_missing_empty_and_out_of_order_sections() -> (
    None
):
    def missing_sections() -> None:
        """Summarize one incomplete public function.

        Inputs:
        The function accepts no public inputs.

        Outputs:
        The function returns ``None``.
        """

    def empty_section() -> None:
        """Summarize one malformed public function.

        Inputs:
        The function accepts no public inputs.

        Outputs:
        The function returns ``None``.

        Failure Modes:

        Scientific Caveats:
        The function does not perform scientific interpretation.
        """

    def out_of_order_section() -> None:
        """Summarize one unordered public function.

        Outputs:
        The function returns ``None``.

        Inputs:
        The function accepts no public inputs.

        Failure Modes:
        The function raises no governed public exceptions.

        Scientific Caveats:
        The function does not perform scientific interpretation.
        """

    report = build_public_function_docstring_report(
        (missing_sections, empty_section, out_of_order_section)
    )

    assert report.function_count == 3
    observations = {item.qualified_name: item for item in report.violating_observations}
    assert len(observations) == 3
    missing_observation = observations[
        f"{__name__}.test_public_function_docstring_report_flags_missing_empty_and_out_of_order_sections.<locals>.missing_sections"
    ]
    assert missing_observation.missing_sections == (
        "Failure Modes:",
        "Scientific Caveats:",
    )
    assert missing_observation.empty_sections == ()
    assert missing_observation.out_of_order_sections == ()
    empty_observation = observations[
        f"{__name__}.test_public_function_docstring_report_flags_missing_empty_and_out_of_order_sections.<locals>.empty_section"
    ]
    assert empty_observation.missing_sections == ()
    assert empty_observation.empty_sections == ("Failure Modes:",)
    assert empty_observation.out_of_order_sections == ()
    unordered_observation = observations[
        f"{__name__}.test_public_function_docstring_report_flags_missing_empty_and_out_of_order_sections.<locals>.out_of_order_section"
    ]
    assert unordered_observation.missing_sections == ()
    assert unordered_observation.empty_sections == ()
    assert unordered_observation.out_of_order_sections == (
        "Outputs:",
        "Inputs:",
        "Failure Modes:",
        "Scientific Caveats:",
    )
