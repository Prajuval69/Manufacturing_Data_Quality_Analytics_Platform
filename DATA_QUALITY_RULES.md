# Implemented data-quality rules

The executed machine-readable catalog is [config/dq_rules.json](config/dq_rules.json). The full field-by-field catalog is [docs/DATA_QUALITY_RULES.md](docs/DATA_QUALITY_RULES.md), and the scoring model is [docs/DQ_SCORING.md](docs/DQ_SCORING.md).

The build implements 159 active rules across completeness, validity, consistency, uniqueness, referential integrity, timeliness and anomaly. Each rule records its source/table/column, severity, phase, blocking behavior and logic parameters. Actual execution evidence and exception counts are in [docs/BUILD_VERIFICATION.md](docs/BUILD_VERIFICATION.md).
