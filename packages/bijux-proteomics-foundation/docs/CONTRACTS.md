# Contracts

Package contracts:

- output of canonical serialization must be deterministic for equivalent models
- schema compatibility checks must return explicit compatibility status and
  reasons
- migration helpers must preserve semantic model meaning across versions

When this package changes, downstream packages should not need behavioral
rewrites unless the schema contract itself intentionally changes.
