# Wiki source-reference validation fix

This patch makes Wiki generation resilient when the LLM returns one or more chunk UUIDs that were not present in the supplied document chunks.

Behavior:
- invalid page-level chunk IDs are filtered out;
- invalid claim-level citations are removed;
- inline citation links for removed claims become plain text;
- page sources fall back to the union of valid claim sources;
- pages with no verifiable source are skipped;
- compilation fails only if no generated page has any verifiable source.

Validation performed:
- Python compilation passed;
- source validation smoke tests passed.
