from __future__ import annotations

import pytest

from bijux_proteomics_dev.release.governance.hostile_review_pages import (
    build_hostile_review_page_set,
    run,
)

pytestmark = pytest.mark.slow


def test_hostile_review_pages_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_hostile_review_page_set_captures_live_release_blockers() -> None:
    pages = build_hostile_review_page_set()

    assert len(pages.family_entries) == 5
    assert pages.blocked_categories
    assert any(group.title == "Workflow-family gaps" for group in pages.blocker_groups)
    assert any(
        "multiplex" in issue for group in pages.blocker_groups for issue in group.issues
    )
