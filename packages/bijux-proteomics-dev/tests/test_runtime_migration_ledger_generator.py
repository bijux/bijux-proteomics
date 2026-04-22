from __future__ import annotations

from bijux_proteomics_dev.quality.architecture.runtime_migration_ledger import run


def test_runtime_migration_ledger_generator_is_up_to_date() -> None:
    assert run(check=True) == 0
