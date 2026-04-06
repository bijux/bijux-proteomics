# Architecture checks

PYTHON      := $(shell command -v python3 || command -v python)

.PHONY: architecture-check

architecture-check:
	@$(PYTHON) scripts/check_architecture_docs.py
	@$(PYTHON) scripts/check_design_debt.py
