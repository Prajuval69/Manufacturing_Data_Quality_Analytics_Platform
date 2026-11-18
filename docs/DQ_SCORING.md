# Transparent project scoring

These are portfolio-specific weights, not an industry standard.

|Bucket|Weight|
|---|---:|
|Completeness|0.30|
|Validity|0.25|
|Consistency|0.20|
|Uniqueness|0.10|
|Referential integrity|0.10|
|Timeliness + anomaly|0.05|

For a group, each dimension pass rate is `SUM(passed checks) / COUNT(checks)`. Timeliness and anomaly checks are pooled into the sixth bucket before taking their pass rate. Overall score is `100 × SUM(weight × bucket pass rate) / SUM(applicable bucket weights)`, rounded to four decimal places. A bucket with no checks is omitted and the remaining weights renormalize. A group with no checks has an unknown score, not an invented 100.

Example: only completeness and validity apply; completeness passes 1/2 checks and validity passes 1/1. Score = `100 × (0.30×0.5 + 0.25×1) / (0.30+0.25) = 72.7273`. Unit tests verify this and timeliness/anomaly pooling.

Denominators include every incoming source occurrence for every active rule on its table, including records later quarantined and duplicates. Null values fail completeness; format/reference/date comparison rules generally defer null failures to completeness rather than reporting a second failure. Canonical formatting/name and uniqueness rules run before repair; other checks evaluate standardized data and accepted parent keys. This is an incoming batch assurance score with clearly identified phases; it does not claim to be a purely raw score or a post-cleaning score.

Scores are recalculated independently for overall, source, table, facility, event month and dimension. Unknown/missing facility identifiers form `UNKNOWN`; masters and fields without a facility form `UNASSIGNED`. Event dates that cannot parse form `UNKNOWN`; master records form `MASTER`. Invalid future dates appear in their own future month. Months represent event cohorts within the current snapshot, not historical executions of the pipeline.

`dq_check` stores check-level evidence. `dq_result` stores checked/passed/failed counts per rule; these reconcile with the exception table. `dq_score` holds grouped results. `outputs/powerbi/dq_summary.csv` exports every scope and `dq_trend.csv` exports month scores. The `verify` command independently recomputes the score from persisted row checks.

A 99+ score is possible while many rows are quarantined: one failed field excludes a record, while many other checks on that row pass. Always show raw count, curated count, quarantine count, failed-rule counts and critical exceptions next to the score. Marking an exception resolved or accepted changes workflow counts, not recorded rule failures or the DQ score. Rebuild after an actual source correction to measure improvement.
