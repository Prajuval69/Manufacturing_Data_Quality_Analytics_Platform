# Optional GenAI data quality assistant

The default assistant is a deterministic interface over structured SQLite evidence. It always works without a key. Validation, cleansing, scoring and KPI calculation never use an LLM.

The service retrieves the DQ run summary, top five failed rules, actionable facility exception counts, executive KPIs, two latest dated cohort scores through the fixed batch as-of date, and matching glossary definitions. Intentionally corrupted future dates stay outside the monthly comparison. If a question contains an exception ID or exact rule ID, it retrieves that record using a bound parameter. All SQL queries are predefined; a question cannot become SQL or execute commands.

Template routing supports common issues, facility ranking, monthly changes, first investigation priorities, exception/rule explanations, KPI definitions and a general summary. Monthly differences are observations, not invented causal conclusions. Unknown facility codes and undated records remain separate. The response returns its structured evidence so the answer is inspectable.

The `Provider` protocol isolates external generation. The optional OpenAI HTTP adapter uses a bounded context, a 20-second timeout and a short response limit. Configure `LLM_PROVIDER=openai`, `LLM_API_KEY` and `LLM_MODEL` in an ignored local `.env`, and explicitly request `use_llm=true`. No default paid model is assumed. The model should be available to the user's account. Keys are never put into context, source files, reports or API responses.

Missing configuration, provider errors or empty responses trigger the same deterministic evidence response, with a sanitized fallback reason. Do not treat generated explanations as source corrections. Test coverage includes no-key behavior, templates, evidence retrieval, a mock provider interface, provider failure and a SQL-injection-style question.

No external provider credential was needed for the verified build. The real external HTTP provider path is implemented but was not exercised against a paid service. Mock tests verify the service boundary; real FastAPI smoke tests exercise deterministic mode. Example questions:

- What are the most common data-quality issues?
- Which facility has the most exceptions?
- Why did data quality decrease this month?
- What does On-Time Delivery Rate mean?
- Explain exception followed by an actual exception ID.
- What should the team investigate first?
