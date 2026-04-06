# Contracts

Modules in this package must be deterministic for the same repository state and
must return non-zero exit codes on contract violations.

Any check used by root `make` targets must emit actionable error text.
