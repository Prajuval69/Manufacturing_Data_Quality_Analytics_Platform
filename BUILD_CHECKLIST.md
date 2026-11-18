# Build Checklist

Codex must verify every item before declaring completion.

## Repository
- [x] Clean project structure
- [x] README
- [x] requirements/pyproject
- [x] .env.example
- [x] .gitignore

## Data
- [x] Synthetic generator
- [x] Reproducible seed
- [x] Multiple source systems
- [x] Controlled defects
- [x] Raw/staging/processed layers

## Database
- [x] Schema
- [x] Master tables
- [x] Fact tables
- [x] DQ tables
- [x] Governance tables
- [x] Analytics tables

## Quality
- [x] Profiling
- [x] Validation
- [x] DQ scoring
- [x] Exception management

## Governance
- [x] Metadata
- [x] Glossary
- [x] Lineage
- [x] Data ownership

## Analytics
- [x] KPIs
- [x] Reporting exports
- [x] Power BI guide

## API
- [x] Health
- [x] KPI endpoints
- [x] DQ endpoints
- [x] Exception endpoints
- [x] Governance endpoints
- [x] Profiling endpoint

## AI
- [x] Structured context retrieval
- [x] Optional LLM
- [x] Deterministic fallback

## Testing
- [x] 25+ meaningful tests
- [x] Integration test
- [x] API test
- [x] Pipeline test
- [x] All tests passing

## Verification
- [x] Full pipeline executed
- [x] Outputs inspected
- [x] API smoke-tested
- [x] No secrets
- [x] Documentation updated

## Actual verification receipt

All items were exercised against the implemented system. See docs/BUILD_VERIFICATION.md and outputs/reports/ for the measured evidence: 84 tests, 37 full-scale acceptance checks and 20 loopback HTTP checks passed. The optional external provider is implemented and mock-tested; credential-free assistant behavior is verified. Power BI delivery is actual CSV datasets plus an implementation guide. Source/output credential checks passed locally; this folder does not contain initialized Git history.


