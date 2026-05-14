include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../proteomics-package.mk

API_MODE := none
PACKAGE_IMPORT_NAME := proteomics_runtime
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-proteomics-dev[dev]" $(MONOREPO_ROOT)/packages/bijux-proteomics-runtime

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
