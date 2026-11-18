# Interview Guide

## 30-second explanation

"I built a fictional manufacturing data platform that combines data engineering, analytics, data quality, and governance. I generated data from simulated ERP, MES, warehouse, and logistics systems, built a Python and SQL pipeline, profiled and validated the data, created an exception-management layer, and produced Power BI-ready analytics. I also added metadata, lineage, a business glossary, and an optional GenAI assistant that explains data-quality issues."

## Why data quality?

"Analytics are only useful when the underlying data is reliable. Instead of only building dashboards, I built validation and exception management so users can see whether they should trust the data."

## Why synthetic data?

"I wanted a realistic portfolio project without using confidential or proprietary company data."

## What is data lineage?

"It describes how data moves from a source through transformations into a reporting or analytics output."

## What is metadata?

"Metadata describes data — for example, a field's business meaning, data type, owner, source, and refresh frequency."

## Why master data?

"Customers, products, facilities, and suppliers are shared reference entities. If those identifiers are inconsistent, downstream reporting becomes unreliable."

## How does the DQ score work?

"I used a transparent project-specific weighted model across completeness, validity, consistency, uniqueness, referential integrity, and anomaly/timeliness dimensions. The weights are documented and are not presented as an industry standard."

## Why GenAI?

"I used GenAI as an additional interface over structured data-quality results. The core validation remains deterministic, while GenAI helps users ask questions and understand the results."

## Why an optional fallback?

"That keeps the system reproducible and prevents the core project from depending on an external API or paid service."

## What would you improve?

- Cloud data warehouse
- CI/CD
- Role-based access
- Real-time ingestion
- Data contracts
- More advanced anomaly detection
- Production LLM guardrails
- Observability
