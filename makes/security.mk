PROJECT_ARTIFACTS_DIR ?= artifacts
SECURITY_PATHS ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
BANDIT ?= $(if $(ACT),$(ACT)/bandit,bandit)
PIP_AUDIT ?= $(if $(ACT),$(ACT)/pip-audit,pip-audit)
SECURITY_IGNORE_IDS ?= PYSEC-2022-42969 CVE-2025-68463
SECURITY_BANDIT_SKIP_IDS ?= B311
SECURITY_PIP_AUDIT_TEXT_COMMAND ?= PYTHONPATH="$(DEV_PYTHONPATH)$${PYTHONPATH:+:$$PYTHONPATH}" "$(VENV_PYTHON)" -m bijux_proteomics_dev.security.pip_audit_gate
SECURITY_EXTRA_TARGETS ?= security-dependency-allowlist

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/security.mk

security-dependency-allowlist:
	@$(DEV_RUN) -m bijux_proteomics_dev.security.dependency_allowlist
.PHONY: security-dependency-allowlist
