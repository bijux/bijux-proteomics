"""Import tests for bijux-proteomics-dev."""

import bijux_proteomics_dev.docs
import bijux_proteomics_dev.governance
import bijux_proteomics_dev.quality
import bijux_proteomics_dev.release
import bijux_proteomics_dev.security
import bijux_proteomics_dev.tools


def test_package_imports() -> None:
    assert bijux_proteomics_dev.governance is not None
    assert bijux_proteomics_dev.docs is not None
    assert bijux_proteomics_dev.quality is not None
    assert bijux_proteomics_dev.release is not None
    assert bijux_proteomics_dev.security is not None
    assert bijux_proteomics_dev.tools is not None
