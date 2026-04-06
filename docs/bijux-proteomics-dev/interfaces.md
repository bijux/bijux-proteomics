# Interfaces

Root `make` targets and CI workflows call package entrypoints through Python
module invocation.

Legacy `scripts/*.py` wrappers remain thin adapters during migration and will be
retired after all gate callers are updated.
