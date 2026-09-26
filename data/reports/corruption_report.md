# Corruption and Repair Comparison

The repaired state is compared with the clean baseline and intentionally corrupted data.

## Metrics

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Samples / rows | 24 | 24 | 24 |
| Unique IDs | 24 | 23 | 24 |
| Missing summaries | 0 | 2 | 0 |
| Duplicate IDs | 0 | 1 | 0 |

## Quality and freshness

| Signal | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Quality gate | PASS | FAIL | PASS |
| Freshness SLA | PASS | PASS | PASS |
| Stale rows | 1 | 1 | 1 |
| Stale ratio | 0.0417 | 0.0417 | 0.0417 |

## Interpretation

- Corrupted data is expected to fail one or more quality/freshness signals and degrade evaluation metrics.
- Repair is successful when the repaired signals and metrics return to, or closely approach, the baseline.
- Repair remains idempotent when it is rebuilt from the trusted raw snapshot rather than mutated corrupted data.
