include $(ROOT_MAKE_DIR)/proteomics-package.mk

PACKAGE_IMPORT_NAME := bijux_proteomics_foundation
PACKAGE_INSTALL_PYTHON_PACKAGES := $(MONOREPO_ROOT)/packages/bijux-proteomics-dev

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
