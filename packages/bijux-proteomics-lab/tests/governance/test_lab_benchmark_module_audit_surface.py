from __future__ import annotations

from bijux_proteomics_lab.governance.charter import (
    DEFAULT_LAB_MODULE_AUDIT,
    LabCharterCapability,
    LabModuleClassification,
)


def test_lab_benchmark_module_audit_keeps_claim_and_rehearsal_modules_operational() -> None:
    benchmark_entries = {
        entry.module_path: entry
        for entry in DEFAULT_LAB_MODULE_AUDIT
        if entry.module_path in {"benchmarks/claims.py", "benchmarks/rehearsals.py"}
    }

    assert set(benchmark_entries) == {"benchmarks/claims.py", "benchmarks/rehearsals.py"}
    assert all(
        entry.classification is LabModuleClassification.OPERATIONAL_VALUE
        for entry in benchmark_entries.values()
    )
    assert all(
        LabCharterCapability.HANDOFF_PACKETS in entry.anchor_capabilities
        for entry in benchmark_entries.values()
    )
