include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/../bijux-py/package-profile.mk
include $(ROOT_MAKE_DIR)/package/proteomics-package.mk

PACKAGE_IMPORT_NAME := bijux_proteomics_knowledge
PACKAGE_INSTALL_PYTHON_PACKAGES := $(MONOREPO_ROOT)/packages/bijux-proteomics-dev $(MONOREPO_ROOT)/packages/bijux-proteomics-foundation

include $(ROOT_MAKE_DIR)/bijux-py/package-gates.mk
