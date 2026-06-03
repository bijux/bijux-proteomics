include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../proteomics-package.mk

PACKAGE_IMPORT_NAME := bijux_proteomics
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-proteomics-dev[dev]" $(MONOREPO_ROOT)/packages/bijux-proteomics-foundation $(MONOREPO_ROOT)/packages/bijux-proteomics-intelligence $(MONOREPO_ROOT)/packages/bijux-proteomics-knowledge $(MONOREPO_ROOT)/packages/bijux-proteomics-lab
CODESPELL = $(VENV_PYTHON) -m codespell_lib -L AAS,DAA

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
