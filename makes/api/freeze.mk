PRANCE ?= $(if $(ACT),$(ACT)/prance,prance)
OPENAPI_SPEC_VALIDATOR ?= $(if $(ACT),$(ACT)/openapi-spec-validator,openapi-spec-validator)
ALL_API_SCHEMAS := $(shell find apis -type f -name "schema.yaml" 2>/dev/null)
API_LINT_DIR_ABS := $(abspath $(API_LINT_DIR))

.PHONY: api api-install api-lint api-freeze openapi-drift api-clean api-test api-serve api-serve-bg api-stop

api: api-install api-lint api-freeze openapi-drift
	@echo "✔ API checks passed"

api-install:
	@echo "→ Installing API tooling"
	@"$(VENV_PYTHON)" -m prance --version >/dev/null
	@"$(VENV_PYTHON)" -m openapi_spec_validator --help >/dev/null

api-lint:
	@if [ -z "$(ALL_API_SCHEMAS)" ]; then echo "✘ No OpenAPI schemas found under apis/*/v1/schema.yaml"; exit 1; fi
	@mkdir -p "$(API_LINT_DIR_ABS)"
	@set -e; \
	for schema in $(ALL_API_SCHEMAS); do \
	  name="$$(echo "$$schema" | tr '/' '_')"; \
	  echo "→ Validating $$schema"; \
	  { \
	    $(PRANCE) validate "$$schema"; \
	    $(OPENAPI_SPEC_VALIDATOR) "$$schema"; \
	  } 2>&1 | tee "$(API_LINT_DIR_ABS)/$$name.log"; \
	done
	@echo "✔ API lint complete"

api-freeze:
	@echo "→ Enforcing API schema freeze contracts"
	@$(DEV_RUN) -m bijux_proteomics_dev.api.freeze_contracts
	@echo "✔ API freeze contracts validated"

openapi-drift:
	@echo "→ Checking OpenAPI drift"
	@$(DEV_RUN) -m bijux_proteomics_dev.api.openapi_drift
	@echo "✔ OpenAPI drift check complete"

api-clean:
	@rm -rf "$(API_ARTIFACTS_DIR)" || true

api-test:
	@echo "→ API_MODE=freeze does not run live HTTP tests"

api-serve:
	@echo "→ API_MODE=freeze does not provide api-serve"

api-serve-bg:
	@echo "→ API_MODE=freeze does not provide api-serve-bg"

api-stop:
	@echo "→ API_MODE=freeze does not provide api-stop"

##@ API
api:            ## Validate and enforce frozen API contracts for all package schemas
api-install:    ## Install API lint tooling
api-lint:       ## Validate OpenAPI schemas under apis/*
api-freeze:     ## Ensure pinned_openapi.json and schema.hash match schema.yaml
openapi-drift:  ## Detect breaking schema changes without version bumps
api-clean:      ## Remove API artifacts
