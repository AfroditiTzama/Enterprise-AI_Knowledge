# IMP-001 — Current Wiki Implementation

## Current Pipeline

The current Build Wiki workflow is:

1. The user selects Build Wiki from the Documents page.
2. The frontend calls:
   `POST /wiki/documents/{document_id}/compile`
3. The API router calls `CompileDocumentWikiCommand`.
4. The command verifies:
   - document ownership
   - document status is PROCESSED
   - stored document chunks exist
5. The command sends only the document title and its chunks to the
   `WikiCompiler`.
6. `OpenRouterWikiCompiler` asks the configured LLM to generate:
   - titles
   - slugs
   - summaries
   - Markdown content
   - supporting chunk IDs
   - relationships between pages generated in the same response
7. The command creates `WikiPage`, `WikiPageSource`, and `WikiPageLink`
   entities.
8. The repository deletes the previous Wiki graph for that document.
9. The repository stores the newly generated graph.
10. The frontend navigates to `/wiki` and lists all Wiki pages.

## Current Data Flow

Document
→ Document chunks
→ OpenRouter Wiki compilation
→ Per-document Wiki graph
→ Database
→ Wiki interface

## Current Behaviour

The implementation currently creates an independent Wiki graph for each
document.

The compiler does not receive:

- existing Wiki pages
- Wiki pages generated from other documents
- existing relationships
- existing sources
- global Wiki topics

Therefore, it cannot decide whether to update, merge, or reuse an existing
page.

## Current Relationship Rules

Related-page relationships:

- are suggested by the LLM
- may reference only pages generated in the same compilation
- are stored as directed page links
- are not automatically made bidirectional
- are not returned by the current Wiki API response
- are not displayed in the frontend

## Current Replacement Strategy

Running Build Wiki again for the same document:

1. deletes the existing page links
2. deletes the existing page sources
3. deletes the existing pages
4. creates a completely new document Wiki graph

The current strategy is therefore:

Rebuild and replace

It is not:

Incrementally update and version

## Current Slug Strategy

Each generated slug receives a document-specific prefix:

`{document_id_prefix}-{generated_slug}`

This prevents database slug collisions between documents.

However, it does not prevent semantic duplicates such as:

- `a1b2c3d4-authentication`
- `f8e7d6c5-authentication`

## Current Frontend

The Wiki frontend currently displays:

- a searchable list of pages
- page title
- page summary
- Markdown content
- shortened document ID

It does not currently display:

- related Wiki pages
- source chunks
- source filenames
- page numbers
- backlinks
- Wiki graph navigation

## Architectural Gap

The current system behaves as:

Document → Independent Wiki pages

The target LLM Wiki should behave as:

New source
→ Search the existing Wiki
→ Update relevant pages
→ Create genuinely new pages
→ Merge overlapping knowledge
→ Preserve source provenance
→ Validate page relationships
→ Record revisions

## Conclusion

The existing implementation already provides strong foundations:

- structured Wiki pages
- chunk-level source references
- stored page relationships
- validated LLM output
- document ownership
- a Wiki browsing interface

The main required evolution is to transform the current per-document
replaceable graph into one interconnected and incrementally maintained Wiki.
