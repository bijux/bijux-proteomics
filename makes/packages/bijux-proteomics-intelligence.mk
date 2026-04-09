include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/../bijux-py/package/bootstrap.mk
include $(ROOT_MAKE_DIR)/proteomics-package.mk

PACKAGE_IMPORT_NAME := bijux_proteomics_intelligence
PACKAGE_INSTALL_PYTHON_PACKAGES := $(MONOREPO_ROOT)/packages/bijux-proteomics-dev $(MONOREPO_ROOT)/packages/bijux-proteomics-foundation $(MONOREPO_ROOT)/packages/bijux-proteomics-core $(MONOREPO_ROOT)/packages/bijux-proteomics-knowledge

include $(ROOT_MAKE_DIR)/bijux-py/package/gates.mk
