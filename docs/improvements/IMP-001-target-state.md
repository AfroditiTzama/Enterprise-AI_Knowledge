# IMP-001 — Target-State LLM Wiki

## Objective

Evolve the current per-document Wiki generation flow into one connected,
incrementally maintained knowledge base.

The system remains:

- single-workspace
- single configured LLM integration through OpenRouter
- grounded in the original uploaded documents and chunks

Multi-tenancy and runtime provider switching are outside the scope.

---

## Target Pipeline

New source
→ text extraction
→ chunking
→ topic and claim analysis
→ search existing Wiki pages
→ decide create / update / merge
→ generate revised Wiki content
→ validate sources
→ validate relationships
→ store the new revision
→ update the Wiki index
→ run health checks

---

## Core Principle

The raw documents remain the evidence layer.

The Wiki becomes an organised knowledge layer above the raw sources.

The Wiki must never replace or remove the original source material.

---

## Target Wiki Behaviour

When a new document is compiled, the system should:

1. Analyse the document chunks.
2. Retrieve potentially related existing Wiki pages.
3. Compare the new knowledge with existing content.
4. Update an existing page when the topic already exists.
5. Create a new page only for a genuinely new topic.
6. Merge complementary information.
7. Preserve all valid source references.
8. Flag possible contradictions instead of silently resolving them.
9. Create links between related pages.
10. Update the global Wiki index.

---

## Target Page Structure

Each Wiki page should include:

- title
- stable slug
- summary
- Markdown content
- page type
- source references
- related pages
- backlinks
- created timestamp
- updated timestamp
- revision number
- status

Possible page statuses:

- DRAFT
- PUBLISHED
- NEEDS_REVIEW
- CONFLICTED
- ARCHIVED

---

## Target Page Types

Initial page types:

- overview
- concept
- process
- system
- component
- policy
- decision
- comparison
- person
- project

The page type helps organise the Wiki and improve retrieval.

---

## Source Provenance

Every Wiki page must remain connected to supporting evidence.

Required provenance fields:

- document ID
- document filename
- chunk ID
- page number when available
- ingestion timestamp

A published Wiki page must have at least one valid source.

---

## Relationship Model

Wiki relationships should support:

- related page links
- backlinks
- parent-child relationships
- prerequisite relationships
- component relationships

Initial implementation will use:

- RELATED_TO
- PART_OF
- DEPENDS_ON

Self-links must be rejected.

Links to missing pages must not be published.

---

## Global Wiki Index

The Wiki should include a navigable index that groups pages by:

- page type
- main topic
- source document
- recently updated pages

The index should not be generated as a normal document-specific Wiki page.

It should be created dynamically from stored Wiki metadata.

---

## Assistant Retrieval Order

The Knowledge Assistant should use:

1. relevant Wiki pages
2. directly related Wiki pages
3. raw document chunks as fallback
4. source verification before answer generation

The Wiki provides organised context.

The raw chunks provide detailed evidence and verification.

---

## Safe Implementation Phases

### IMP-001A — Display Existing Relationships

No database redesign.

- Return related pages from the Wiki API.
- Display clickable related pages.
- Allow navigation between related pages.
- Display source references.
- Add backlinks dynamically.

### IMP-001B — Relationship Validation

- Reject self-links.
- Ignore missing page targets.
- Remove duplicate links.
- Optionally create bidirectional RELATED_TO links.
- Add unit tests.

### IMP-001C — Global Wiki Index

- Add page-type metadata.
- Create a dynamic Wiki index.
- Group pages by topic and type.
- Improve Wiki navigation.

### IMP-001D — Existing Wiki Retrieval

- Retrieve existing Wiki pages before compilation.
- Pass relevant existing pages to the compiler.
- Limit context to the most relevant pages.
- Preserve the current raw-chunk input.

### IMP-001E — Create or Update Decisions

The compiler should return operations:

- CREATE
- UPDATE
- MERGE
- NO_CHANGE
- FLAG_CONFLICT

The application layer should validate each operation before persistence.

### IMP-001F — Revision History

- Store page revisions.
- Preserve previous content.
- Record sources added or removed.
- Support rollback.
- Display page history.

### IMP-001G — Wiki Health Check

Detect:

- pages without sources
- broken links
- orphan pages
- probable duplicates
- conflicting claims
- stale pages

---

## First Implementation Boundary

The first code change will be IMP-001A only.

It will not modify:

- document processing
- embeddings
- OpenRouter prompts
- database migrations
- compilation behaviour
- Assistant retrieval

It will only expose and display data that already exists:

- Wiki links
- Wiki sources
- related-page navigation

This minimises regression risk.

---

## Acceptance Criteria for IMP-001A

- The Wiki API returns related pages.
- The Wiki API returns source information.
- Related pages appear as clickable links.
- Clicking a related page opens it.
- Backlinks are visible.
- Invalid links do not break the page.
- The current Build Wiki process continues to work.
- The Assistant continues to work.
- No database migration is required.

---

## Non-Goals

The following are not part of the initial implementation:

- multi-tenancy
- provider switching
- multiple provider adapters
- automatic conflict resolution
- complete semantic deduplication
- billing
- advanced RBAC
