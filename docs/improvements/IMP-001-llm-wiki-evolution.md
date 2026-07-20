# IMP-001 — LLM Wiki Evolution

## Status

PLANNED

## Priority

HIGH

## Current State

The current system processes one document and asks the LLM to generate one or
more Wiki pages from that document.

Generated pages contain:

- title
- slug
- summary
- Markdown content
- source chunk references
- related page slugs

The pages are stored in the database and displayed in a two-column Wiki
interface.

However, the current implementation behaves mainly as:

Document → Independent Wiki pages

It does not yet maintain one evolving and interconnected knowledge base across
multiple uploaded documents.

## Problem

When several related documents are uploaded, the system may:

- create duplicate pages
- create pages with overlapping topics
- fail to update an existing relevant page
- create incomplete links between pages
- keep related knowledge separated by document
- fail to identify conflicting information

The frontend also does not clearly expose the Wiki as a connected network of
pages.

## Goal

Transform the current Wiki into an evolving LLM-maintained knowledge layer.

When a new source is ingested, the system should:

1. Analyse the new source.
2. Search the existing Wiki for related pages.
3. Update relevant pages where appropriate.
4. Create new pages only for genuinely new topics.
5. Create valid links between related pages.
6. Preserve exact source and chunk references.
7. Detect possible duplicates and conflicts.
8. Record the compilation result.

## Proposed Pipeline

Source upload
→ Text extraction
→ Chunking
→ Existing Wiki retrieval
→ Topic and claim analysis
→ Create / update / merge decision
→ Wiki page generation
→ Link validation
→ Source validation
→ Persistence
→ Wiki health check

## Initial Scope

The first implementation will focus on:

- clickable related Wiki pages
- bidirectional page links
- duplicate title and slug prevention
- global Wiki index
- source visibility
- validation of generated page relationships

## Non-Goals

The following are not part of IMP-001:

- multi-tenancy
- organization management
- runtime provider switching
- multiple provider adapters
- billing
- advanced RBAC
- complete automatic conflict resolution

## Acceptance Criteria

IMP-001 is complete when:

- related pages are displayed as clickable links
- selecting a related page opens that page
- page relationships are stored correctly
- self-links are rejected
- missing page links are ignored or reported
- duplicate slugs cannot be created
- every published page has at least one valid source
- the Wiki includes a navigable index
- existing document processing continues to work
- automated tests cover Wiki link validation

## Risks

- The LLM may generate invalid page slugs.
- The LLM may reference pages that were not created.
- Duplicate topics may use different titles.
- Automatic merging may remove important details.
- Cross-document synthesis may introduce unsupported claims.

## Validation Strategy

- Unit tests for page-link validation.
- Repository tests for stored relationships.
- API tests for Wiki compilation.
- Manual test using two documents with overlapping topics.
- Verification that every generated claim remains traceable to source chunks.

## Final Result

To be completed after implementation.
