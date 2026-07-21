# ADR-001 — Use an LLM Wiki as an Organised Knowledge Layer

## Status

Accepted

## Context

The platform currently stores raw documents, extracted chunks, embeddings, Wiki
pages, Wiki sources, and Wiki links.

A traditional vector-only RAG pipeline can retrieve relevant chunks, but it does
not automatically organise knowledge into stable concepts, processes, entities,
and relationships.

## Decision

The system will retain raw documents and chunks as the primary evidence layer.

An LLM-maintained Wiki will be used as an additional organised knowledge layer
above the raw sources.

The Assistant will follow this retrieval order:

1. Relevant Wiki pages.
2. Related Wiki page links.
3. Vector retrieval from raw document chunks.
4. Source verification before answer generation.

The Wiki will not replace the original documents.

## Consequences

### Positive

- Better organisation of knowledge.
- Easier navigation for users.
- Reusable thematic pages.
- Clear links between related concepts.
- More structured context for the Assistant.
- Stronger differentiation from a basic RAG chatbot.

### Negative

- Additional LLM processing cost.
- Risk of information loss during summarisation.
- Need for duplicate and conflict detection.
- Need for Wiki versioning and validation.
- Increased implementation complexity.

## Safeguards

- Preserve immutable source documents.
- Preserve chunk-level provenance.
- Require sources for published Wiki pages.
- Use raw chunks as retrieval fallback.
- Validate links, titles, slugs, and citations.
