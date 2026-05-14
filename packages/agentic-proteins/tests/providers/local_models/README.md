# Real Local Tests  

These tests run **real local structure models** (ESMFold, RoseTTAFold) via the CLI.  

Purpose:  
- Confirm local providers load and execute end-to-end.  
- Produce a real PDB artifact and compute metrics from coordinates.  
- Validate artifact layout and report payloads.  

Requirements:  
- Local model weights and dependencies installed.  
- GPU is optional but strongly recommended for speed.  
- Docker is required for the RoseTTAFold provider when using its docker mode.  

How to run:  
```
pytest packages/agentic-proteins/tests/providers/local_models -m real -s
```

Notes:  
- These tests are **not run in CI**.  
- They are slow and resource-intensive by design.  
