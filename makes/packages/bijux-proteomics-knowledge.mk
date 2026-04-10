include $(ROOT_MAKE_DIR)/proteomics-package.mk

PACKAGE_IMPORT_NAME := bijux_proteomics_knowledge
PACKAGE_INSTALL_PYTHON_PACKAGES := "$(MONOREPO_ROOT)/packages/bijux-proteomics-dev[dev]" $(MONOREPO_ROOT)/packages/bijux-proteomics-foundation

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
