# Enterprise AI Knowledge Assistant — Improvement Roadmap

## Project Direction

The platform remains a single-workspace AI knowledge system.

The project will continue using one configured LLM integration through
OpenRouter. Multi-tenancy and runtime provider switching are outside the
current scope.

The main goal is to evolve the existing document assistant into a reliable
LLM-maintained Wiki with connected pages, source traceability, improved
retrieval, evaluation, and production stability.

---

## Phase 1 — Stabilization

- Return correct HTTP status codes for authentication errors.
- Improve frontend API error messages.
- Add backend unit and API tests.
- Verify reliable local and online execution.
- Document environment and deployment requirements.

## Phase 2 — Wiki Graph

- Display related Wiki pages as clickable links.
- Create bidirectional relationships between pages.
- Prevent broken and self-referencing links.
- Add a global Wiki index.
- Preserve source documents and chunk references.

## Phase 3 — LLM Wiki Ingestion

- Analyse each new source against the existing Wiki.
- Update existing pages before creating new pages.
- Detect similar or duplicate topics.
- Merge complementary information.
- Flag contradictory information.
- Record every Wiki compilation operation.

## Phase 4 — Cross-Document Knowledge

- Generate pages using evidence from multiple documents.
- Preserve provenance for every source.
- Support page revisions and version history.
- Detect outdated or superseded information.
- Add Wiki health checks.

## Phase 5 — Retrieval

- Use Wiki-first retrieval.
- Follow related-page links.
- Use vector retrieval as fallback.
- Evaluate hybrid retrieval where useful.
- Measure retrieval accuracy and citation correctness.

## Phase 6 — Observability and Evaluation

- Record LLM latency.
- Record token usage.
- Estimate request cost.
- Track failures and retries.
- Build a small evaluation dataset.
- Measure answer faithfulness and source correctness.

## Phase 7 — Frontend Improvements

- Improve Wiki navigation.
- Add source and relationship panels.
- Add compilation progress indicators.
- Add clearer empty, loading, and error states.
- Add document-to-Wiki navigation.
