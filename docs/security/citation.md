# citation  

**Scope:** Citation metadata and release citation artifacts.  
**Audience:** Contributors and release operators.  
**Guarantees:** `CITATION.cff` matches the release version and repository URL.  
**Non-Goals:** Reference manager tutorials.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the citation surface for releases.  
Canonical metadata lives in [CITATION.cff](https://github.com/bijux/bijux-proteomics/blob/main/CITATION.cff).  
Citation artifacts are generated via [makefiles/citation.mk](https://github.com/bijux/bijux-proteomics/blob/main/makefiles/citation.mk).  

## Contracts  
Each statement is a contract.  
Contracts align with [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  
Contracts link to [Threat Model](threat_model.md) and [Dependencies](dependencies.md).  
- `CITATION.cff` is the canonical source of citation metadata.  
- `make citation` validates CFF and produces the other formats.  
- Release tags align with `CITATION.cff` version values.  

## Invariants  
Invariants describe stable behavior.  
Checks align with [scripts/check_changelog_version.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_changelog_version.py).  
Invariants align with [Dependencies](dependencies.md).  
- Citation metadata uses the repository URL and SPDX license.  
- Authors list includes the canonical ORCID record.  
- Citation artifacts stay in sync with `CITATION.cff`.  

## Failure Modes  
Failures are explicit and tested.  
Failure coverage aligns with [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  
Failures align with [Docs Style](../meta/DOCS_STYLE.md).  
- Release metadata drift triggers a CI failure.  
- Missing citation files block release publishing.  
- Invalid CFF schema fails validation.  

## Extension Points  
Extensions require tests and docs.  
Extensions are tracked in [Dependencies](dependencies.md).  
Extensions align with [scripts/check_changelog_version.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_changelog_version.py).  
- New citation formats require updates to `makefiles/citation.mk`.  
- New metadata fields require `CITATION.cff` changes.  

## Exit Criteria  
This doc becomes obsolete when citation artifacts are generated elsewhere.  
The replacement is linked in [Docs Style](../meta/DOCS_STYLE.md).  
Obsolete docs are removed.  

Code refs: [tests/unit/test_docs_contract.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/test_docs_contract.py).  
