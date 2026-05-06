from __future__ import annotations

from bijux_proteomics_dev.release.governance.compatibility_ledger import run


def test_compatibility_ledger_generator_is_up_to_date() -> None:
    assert run(check=True) == 0
