# Architecture checks

PYTHON      := $(shell command -v python3 || command -v python)

.PHONY: architecture-check

architecture-check:
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.architecture_docs
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.design_debt
