# Implemented architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the actual component diagram, module responsibilities, snapshot publication, rerun behavior and limitations.

Seeded synthetic ERP/MES/WMS/logistics/master CSVs → contract-checked staging → profiling and canonical standardization → deterministic validation → curated SQLite tables and quarantine/exception evidence → analytics/governance → CSV reporting and FastAPI → optional structured-data assistant.
