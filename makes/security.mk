# Security Configuration (no SBOM here; SBOM is handled in sbom.mk)

SECURITY_PATHS           ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
BANDIT                   ?= $(if $(ACT),$(ACT)/bandit,bandit)
PIP_AUDIT                ?= $(if $(ACT),$(ACT)/pip-audit,pip-audit)
VENV_PYTHON              ?= $(if $(VIRTUAL_ENV),$(VIRTUAL_ENV)/bin/python,python)

SECURITY_REPORT_DIR      ?= artifacts/security
BANDIT_JSON              := $(SECURITY_REPORT_DIR)/bandit.json
BANDIT_TXT               := $(SECURITY_REPORT_DIR)/bandit.txt
PIPA_JSON                := $(SECURITY_REPORT_DIR)/pip-audit.json
PIPA_TXT                 := $(SECURITY_REPORT_DIR)/pip-audit.txt

SECURITY_IGNORE_IDS      ?= PYSEC-2022-42969 CVE-2025-68463
SECURITY_IGNORE_FLAGS     = $(foreach V,$(SECURITY_IGNORE_IDS),--ignore-vuln $(V))
PIP_AUDIT_CONSOLE_FLAGS  ?= --skip-editable --progress-spinner off
PIP_AUDIT_INPUTS         ?=
SECURITY_STRICT          ?= 1

BANDIT_EXCLUDES          ?= .venv,venv,build,dist,.tox,.mypy_cache,.pytest_cache
BANDIT_THREADS           ?= 0

.PHONY: security security-bandit security-audit security-deps security-clean

security: security-bandit security-audit security-deps

security-bandit:
	@mkdir -p "$(SECURITY_REPORT_DIR)"
	@echo "→ Bandit (Python static analysis)"
	@$(BANDIT) -r $(SECURITY_PATHS) -x "$(BANDIT_EXCLUDES)" --skip B311 -f json -o "$(BANDIT_JSON)" -n $(BANDIT_THREADS) || true
	@$(BANDIT) -r $(SECURITY_PATHS) -x "$(BANDIT_EXCLUDES)" --skip B311 -n $(BANDIT_THREADS) | tee "$(BANDIT_TXT)"

security-audit:
	@mkdir -p "$(SECURITY_REPORT_DIR)"
	@echo "→ Pip-audit (dependency vulnerability scan)"
	@set -e; RC=0; \
	$(PIP_AUDIT) $(SECURITY_IGNORE_FLAGS) $(PIP_AUDIT_CONSOLE_FLAGS) $(PIP_AUDIT_INPUTS) \
	  -f json -o "$(PIPA_JSON)" >/dev/null 2>&1 || RC=$$?; \
	if [ $$RC -ne 0 ]; then \
	  echo "!  pip-audit invocation failed (rc=$$RC)"; \
	  if [ "$(SECURITY_STRICT)" = "1" ]; then exit $$RC; fi; \
	fi
	@set -o pipefail; \
	PIPA_JSON="$(PIPA_JSON)" \
	SECURITY_STRICT="$(SECURITY_STRICT)" \
	SECURITY_IGNORE_IDS="$(SECURITY_IGNORE_IDS)" \
	PYTHONPATH="$(DEV_PYTHONPATH)$${PYTHONPATH:+:$$PYTHONPATH}" \
	"$(VENV_PYTHON)" -m bijux_proteomics_dev.security.pip_audit_gate | tee "$(PIPA_TXT)"

security-deps:
	@$(DEV_RUN) -m bijux_proteomics_dev.security.dependency_allowlist

security-clean:
	@rm -rf "$(SECURITY_REPORT_DIR)"

##@ Security
security:        ## Run Bandit and pip-audit; save reports to $(SECURITY_REPORT_DIR)
security-bandit: ## Run Bandit (screen + JSON artifact)
security-audit:  ## Run pip-audit (JSON once) and gate via scripts/helper_pip_audit.py; prints concise summary
security-clean:  ## Remove security reports
