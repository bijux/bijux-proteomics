# NAMING  

**Scope:** Canonical naming registry.  
**Audience:** Contributors and reviewers.  
**Guarantees:** Names and casing are enforced.  
**Non-Goals:** Domain theory.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines canonical names.  
Architecture components are defined in [Architecture](../architecture/architecture.md).  
Read [Docs Style](DOCS_STYLE.md) before edits.  
Read [Docs Voice](DOCS_VOICE.md) for voice rules.  

## Contracts  
Canonical names are listed below.  
Forbidden aliases are listed below.  
Capitalization follows the canonical list.  

## Invariants  
Each concept has one canonical name.  
Aliases are rejected in docs.  
Casing is enforced by CI.  

## Failure Modes  
Alias usage fails docs lint.  
Casing drift fails docs lint.  
Undefined names fail reviews.  

## Extension Points  
Naming changes occur in this file.  
Naming changes update [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).  
Naming changes update [Triage](TRIAGE.md).  

## Exit Criteria  
This doc becomes obsolete when naming is generated.  
The replacement is [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).  
Obsolete docs are removed.  

Canonical names:  
- CLI  
- API  
- run_id  
- artifacts  
- agent  
- tool  
- policy  
- execution unit  
- evaluation artifact  
- protein  
- signal  
- pathway  
- regulation  
- cell  

Forbidden aliases:  
- command line  
- endpoint  
- run id  
- artifact directory  
- execution-unit  
- evaluation output  

Code refs: [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).  
