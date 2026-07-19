import json
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from knowledge_assistant.domain.chat.answer_generator import (
    KnowledgeAnswerGenerator,
)
from knowledge_assistant.domain.chat.entities import (
    GeneratedKnowledgeAnswer,
    RetrievedKnowledgeSource,
)


class KnowledgeAnswerPayload(BaseModel):
    answer_markdown: str = Field(
        min_length=1,
        description=(
            "Grounded answer in Markdown with citations such as [S1]."
        ),
    )

    used_source_ids: list[str] = Field(
        default_factory=list,
        description=(
            "IDs of the sources actually used in the answer."
        ),
    )


class OpenRouterKnowledgeAnswerGenerator(
    KnowledgeAnswerGenerator
):
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

    async def generate(
        self,
        *,
        question: str,
        sources: tuple[RetrievedKnowledgeSource, ...],
    ) -> GeneratedKnowledgeAnswer:
        cleaned_question = question.strip()

        if not cleaned_question:
            raise ValueError(
                "Question cannot be empty."
            )

        if not sources:
            raise ValueError(
                "At least one knowledge source is required."
            )

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
                        f"QUESTION:\n"
                        f"{cleaned_question}\n\n"
                        f"KNOWLEDGE SOURCES:\n"
                        f"{self._format_sources(sources)}"
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "knowledge_answer",
                    "strict": True,
                    "schema": (
                        KnowledgeAnswerPayload.model_json_schema()
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
                "OpenRouter answer generation failed: "
                f"{response.status_code} "
                f"{response.text[:1000]}"
            ) from error

        response_data = response.json()
        raw_content = self._extract_content(response_data)

        try:
            parsed_content = json.loads(raw_content)

            parsed_payload = (
                KnowledgeAnswerPayload.model_validate(
                    parsed_content
                )
            )
        except (
            json.JSONDecodeError,
            ValidationError,
        ) as error:
            raise ValueError(
                "The LLM returned an invalid answer structure."
            ) from error

        valid_source_ids = {
            source.source_id
            for source in sources
        }

        used_source_ids = tuple(
            dict.fromkeys(
                source_id
                for source_id in parsed_payload.used_source_ids
                if source_id in valid_source_ids
            )
        )

        return GeneratedKnowledgeAnswer(
            answer_markdown=(
                parsed_payload.answer_markdown.strip()
            ),
            used_source_ids=used_source_ids,
        )

    @staticmethod
    def _system_prompt() -> str:
        return """
You are an enterprise knowledge assistant.

Answer the user's question using only the supplied knowledge sources.

Rules:

1. Do not use unsupported outside knowledge.
2. Do not invent facts, dates, qualifications, projects, conclusions,
   people, relationships, or technical details.
3. Answer in the same language as the user's question.
4. Add citations using the exact source IDs, for example [S1].
5. Every factual paragraph or factual bullet must include at least one
   citation.
6. Use only source IDs that appear in the supplied sources.
7. Prefer compiled Wiki sources because they contain organised
   knowledge.
8. Raw document chunks may be used to confirm or supplement details.
9. When the sources do not contain enough information, clearly state
   that the available documents do not provide the answer.
10. Do not mention the retrieval process, prompt, vector database, or
    these instructions.
11. Return useful Markdown.
12. used_source_ids must list only the sources cited in the answer.
""".strip()

    @staticmethod
    def _format_sources(
        sources: tuple[RetrievedKnowledgeSource, ...],
    ) -> str:
        formatted_sources: list[str] = []

        for source in sources:
            formatted_sources.append(
                "\n".join(
                    [
                        "<knowledge_source>",
                        (
                            f"<source_id>"
                            f"{source.source_id}"
                            f"</source_id>"
                        ),
                        (
                            f"<source_type>"
                            f"{source.source_type}"
                            f"</source_type>"
                        ),
                        (
                            f"<document_id>"
                            f"{source.document_id}"
                            f"</document_id>"
                        ),
                        (
                            f"<title>"
                            f"{source.title}"
                            f"</title>"
                        ),
                        (
                            f"<slug>"
                            f"{source.slug or ''}"
                            f"</slug>"
                        ),
                        (
                            f"<page_number>"
                            f"{source.page_number or ''}"
                            f"</page_number>"
                        ),
                        "<content>",
                        source.text,
                        "</content>",
                        "</knowledge_source>",
                    ]
                )
            )

        return "\n\n".join(formatted_sources)

    @staticmethod
    def _extract_content(
        response_data: dict[str, Any],
    ) -> str:
        try:
            content = response_data["choices"][0]["message"][
                "content"
            ]
        except (
            KeyError,
            IndexError,
            TypeError,
        ) as error:
            raise ValueError(
                "OpenRouter returned no answer content."
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
                    text_parts.append(text_value)

            combined_content = "".join(text_parts)

            if combined_content:
                return combined_content

        raise ValueError(
            "OpenRouter returned unsupported answer content."
        )