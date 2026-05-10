include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../proteomics-package.mk

PACKAGE_IMPORT_NAME := bijux_proteomics_alias
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-proteomics-dev[dev]" $(MONOREPO_ROOT)/packages/bijux-proteomics-core

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
