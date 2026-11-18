# Codex Execution Instructions

Read `MASTER_PROMPT.md` first.

Then read every `.md` file in this package before implementation.

## Execution behavior

Do not ask the user to manually implement individual modules unless a genuine environment limitation blocks progress.

Inspect the workspace first.

Build the complete project.

Prefer working code over elaborate scaffolding.

After each major stage:
1. run it,
2. inspect the output,
3. fix errors,
4. continue.

At the end:
- run the complete pipeline,
- run the full test suite,
- verify the database,
- verify generated CSV/Excel files,
- smoke-test the API,
- verify no credentials are committed,
- update documentation with actual results.

If Power BI Desktop is unavailable, generate the import-ready datasets and Power BI guide instead of pretending to generate a PBIX file.

If an external LLM is unavailable, implement and demonstrate the deterministic assistant fallback.

Do not stop at code generation.
