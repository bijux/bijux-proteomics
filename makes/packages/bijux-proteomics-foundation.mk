include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../proteomics-package.mk

PACKAGE_IMPORT_NAME := bijux_proteomics_foundation
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-proteomics-dev[dev]"

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
