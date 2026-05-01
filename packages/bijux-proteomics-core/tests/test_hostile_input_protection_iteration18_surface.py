# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration_iteration18 import (
    HostileInputProtectionInput,
    run_hostile_input_protection,
)


def test_run_hostile_input_protection_refuses_unsafe_inputs() -> None:
    report = run_hostile_input_protection(
        HostileInputProtectionInput(
            archive_members=("../secrets.env", "raw/unsafe;name.tsv"),
            record_sizes_bytes=(12, 8_000_001),
            xml_payloads=("<!DOCTYPE data [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>",),
            table_rows=("id\tvalue", "a\tb\tc"),
            max_record_size_bytes=1_000_000,
        )
    )

    codes = {issue.code for issue in report.issues}

    assert report.accepted is False
    assert "path_traversal" in codes
    assert "hostile_filename" in codes
    assert "oversized_record" in codes
    assert "xml_entity_abuse" in codes
    assert "corrupt_table" in codes
