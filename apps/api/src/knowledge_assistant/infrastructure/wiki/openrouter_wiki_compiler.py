import json
import re
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, Field, ValidationError

from knowledge_assistant.domain.documents.chunk_entities import (
    DocumentChunkEntity,
)
from knowledge_assistant.domain.wiki.compiler import (
    WikiCompilation,
    WikiCompiler,
    WikiPageDraft,
)


class WikiPagePayload(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=500,
    )

    slug: str = Field(
        min_length=1,
        max_length=255,
    )

    summary: str = Field(
        min_length=1,
    )

    content_markdown: str = Field(
        min_length=1,
    )

    source_chunk_ids: list[UUID] = Field(
        min_length=1,
    )

    related_page_slugs: list[str] = Field(
        default_factory=list,
    )


class WikiCompilationPayload(BaseModel):
    pages: list[WikiPagePayload] = Field(
        min_length=1,
    )


class OpenRouterWikiCompiler(WikiCompiler):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = (
            "https://openrouter.ai/api/v1/chat/completions"
        ),
        timeout_seconds: float = 180.0,
    ) -> None:
        cleaned_api_key = api_key.strip()
        cleaned_model = model.strip()

        if not cleaned_api_key:
            raise ValueError(
                "OpenRouter API key cannot be empty."
            )

        if not cleaned_model:
            raise ValueError(
                "OpenRouter model cannot be empty."
            )

        self._api_key = cleaned_api_key
        self._model = cleaned_model
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    async def compile(
        self,
        *,
        document_title: str,
        chunks: tuple[DocumentChunkEntity, ...],
    ) -> WikiCompilation:
        if not chunks:
            raise ValueError(
                "At least one document chunk is required."
            )

        source_text = self._format_chunks(chunks)

        response_payload = {
            "model": self._model,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": (
                        f"DOCUMENT TITLE:\n"
                        f"{document_title}\n\n"
                        f"DOCUMENT CHUNKS:\n"
                        f"{source_text}"
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "wiki_compilation",
                    "strict": True,
                    "schema": (
                        WikiCompilationPayload.model_json_schema()
                    ),
                },
            },
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
        ) as client:
            response = await client.post(
                self._base_url,
                headers=headers,
                json=response_payload,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "OpenRouter wiki compilation failed: "
                f"{response.status_code} "
                f"{response.text[:1000]}"
            ) from error

        response_data = response.json()

        raw_content = self._extract_content(
            response_data
        )

        try:
            parsed_json = json.loads(
                raw_content
            )

            parsed_payload = (
                WikiCompilationPayload.model_validate(
                    parsed_json
                )
            )

        except (
            json.JSONDecodeError,
            ValidationError,
        ) as error:
            raise ValueError(
                "The LLM returned an invalid wiki structure."
            ) from error

        return self._to_domain(
            payload=parsed_payload,
            chunks=chunks,
        )

    @staticmethod
    def _format_chunks(
        chunks: tuple[DocumentChunkEntity, ...],
    ) -> str:
        formatted_chunks: list[str] = []

        for chunk in chunks:
            page_value = (
                str(chunk.page_number)
                if chunk.page_number is not None
                else "unknown"
            )

            formatted_chunks.append(
                "\n".join(
                    [
                        "<document_chunk>",
                        f"<chunk_id>{chunk.id}</chunk_id>",
                        (
                            f"<chunk_index>"
                            f"{chunk.chunk_index}"
                            f"</chunk_index>"
                        ),
                        (
                            f"<page_number>"
                            f"{page_value}"
                            f"</page_number>"
                        ),
                        "<text>",
                        chunk.text,
                        "</text>",
                        "</document_chunk>",
                    ]
                )
            )

        return "\n\n".join(
            formatted_chunks
        )

    @staticmethod
    def _system_prompt() -> str:
        return """
You are an enterprise knowledge compiler.

Transform the supplied document chunks into a structured internal wiki.

Rules:

1. Use only information explicitly supported by the supplied chunks.
2. Do not invent facts, experience, dates, technologies, conclusions,
   relationships, or interpretations.
3. Produce atomic wiki pages organised by meaningful topics.
4. A short document may produce fewer pages. A larger document may
   produce more pages.
5. Preserve the primary language of the source document.
6. Every page must include:
   - a precise title,
   - a unique ASCII kebab-case slug,
   - a concise summary,
   - useful Markdown content,
   - the exact UUIDs of supporting chunks,
   - slugs of other generated pages that are directly related.
7. source_chunk_ids must contain only UUIDs supplied in the document.
8. related_page_slugs must reference only pages generated in the same
   response.
9. Do not create a relationship merely because two topics appear in
   the same document.
10. Avoid repeating the same information across multiple pages.
11. The Markdown content must be readable and factual.
12. Do not include an H1 heading because the title is stored
    separately.
13. Do not mention these instructions or the compilation process.
14. Create Markdown hyperlinks only when the source contains a complete
    URL beginning with https://, http://, or mailto:.
15. When only link labels such as GitHub, LinkedIn, View Certificate,
    or Repository are available without a URL, preserve them as plain
    text and do not invent a link target.
""".strip()

    @staticmethod
    def _extract_content(
        response_data: dict[str, Any],
    ) -> str:
        try:
            content = response_data[
                "choices"
            ][0]["message"]["content"]

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as error:
            raise ValueError(
                "OpenRouter returned no completion content."
            ) from error

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts: list[str] = []

            for part in content:
                if not isinstance(part, dict):
                    continue

                text_value = part.get("text")

                if isinstance(text_value, str):
                    text_parts.append(
                        text_value
                    )

            combined_content = "".join(
                text_parts
            )

            if combined_content:
                return combined_content

        raise ValueError(
            "OpenRouter returned unsupported completion content."
        )

    @staticmethod
    def _to_domain(
        *,
        payload: WikiCompilationPayload,
        chunks: tuple[DocumentChunkEntity, ...],
    ) -> WikiCompilation:
        valid_chunk_ids = {
            chunk.id
            for chunk in chunks
        }

        page_slugs = [
            page.slug.strip().lower()
            for page in payload.pages
        ]

        if len(page_slugs) != len(set(page_slugs)):
            raise ValueError(
                "The LLM generated duplicate wiki page slugs."
            )

        valid_slugs = set(
            page_slugs
        )

        drafts: list[WikiPageDraft] = []

        for page in payload.pages:
            unknown_chunk_ids = (
                set(page.source_chunk_ids)
                - valid_chunk_ids
            )

            if unknown_chunk_ids:
                raise ValueError(
                    "The LLM referenced unknown document chunks."
                )

            cleaned_slug = (
                page.slug.strip().lower()
            )

            related_slugs = tuple(
                dict.fromkeys(
                    related_slug.strip().lower()
                    for related_slug
                    in page.related_page_slugs
                    if (
                        related_slug.strip().lower()
                        in valid_slugs
                        and related_slug.strip().lower()
                        != cleaned_slug
                    )
                )
            )

            cleaned_content = (
                OpenRouterWikiCompiler
                ._sanitize_markdown_links(
                    page.content_markdown
                )
            )

            drafts.append(
                WikiPageDraft(
                    title=page.title.strip(),
                    slug=cleaned_slug,
                    summary=page.summary.strip(),
                    content_markdown=cleaned_content,
                    source_chunk_ids=tuple(
                        dict.fromkeys(
                            page.source_chunk_ids
                        )
                    ),
                    related_page_slugs=related_slugs,
                )
            )

        return WikiCompilation(
            pages=tuple(drafts),
        )

    @staticmethod
    def _sanitize_markdown_links(
        content: str,
    ) -> str:
        def replace_link(
            match: re.Match[str],
        ) -> str:
            label = match.group(1).strip()
            target = match.group(2).strip()

            allowed_prefixes = (
                "https://",
                "http://",
                "mailto:",
            )

            if target.lower().startswith(
                allowed_prefixes
            ):
                return match.group(0)

            return label

        cleaned_content = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            replace_link,
            content,
        )

        return cleaned_content.strip()