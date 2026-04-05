# DOCS_STYLE  

**Scope:** Documentation style contract for docs/.  
**Audience:** Contributors editing docs.  
**Guarantees:** Docs follow a single structure and voice.  
**Non-Goals:** Narrative guidance, marketing, or philosophy.  
Why: This doc exists to record its single responsibility for review.  

## Overview  
This doc defines the documentation structure.  
Architecture components are defined in [Architecture](../architecture/architecture.md).  
Read [Docs Voice](DOCS_VOICE.md) for voice rules.  
Read [Triage](TRIAGE.md) for lifecycle rules.  

## Contracts  
Section order is Overview, Contracts, Invariants, Failure Modes, Extension Points, Exit Criteria.  
Allowed section names match the order list.  
Max section depth is H2.  

## Invariants  
Each doc has the front-matter block.  
Each section has three sentences or a table.  
Each doc links to two docs and one code artifact.  

## Failure Modes  
Style violations fail docs lint.  
Style violations block CI.  
Style violations require a rewrite.  

## Extension Points  
Style changes occur in this file.  
Style changes update [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).  
Style changes update [Docs Voice](DOCS_VOICE.md).  

## Exit Criteria  
This doc becomes obsolete when docs are generated.  
The replacement is [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).  
Obsolete docs are removed.  

Code refs: [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).  
