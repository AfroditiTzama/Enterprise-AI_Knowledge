# Validation

Completed in the patch environment:

- Python compilation for the backend source tree.
- Processing-job domain lifecycle tests: 3 passed.
- Processing-job mapper round-trip smoke test.
- Pydantic response-schema smoke test.
- TypeScript syntax transpilation for changed frontend files.
- TypeScript strict check against local dependency stubs for changed frontend files.
- CSS brace-balance check.

The full backend suite and Vite production build require the project's installed dependencies and must be run in the project's Python 3.12 virtual environment and frontend workspace before deployment.
