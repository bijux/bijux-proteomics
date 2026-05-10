include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../proteomics-package.mk

PACKAGE_IMPORT_NAME := proteomics_lab
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-proteomics-dev[dev]" $(MONOREPO_ROOT)/packages/bijux-proteomics-lab

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
