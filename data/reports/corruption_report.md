# Corruption and Repair Report

The repaired dataset is rebuilt from the trusted raw snapshot.

| State | Rows | Unique IDs | Missing summaries | Duplicate IDs |
|---|---:|---:|---:|---:|
| Baseline | 24 | 24 | 0 | 0 |
| Corrupted | 24 | 23 | 2 | 1 |
| Repaired | 24 | 24 | 0 | 0 |

Repair is idempotent because it never uses the corrupted dataframe as its source.
