import json
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from knowledge_assistant.domain.wiki.compiler import WikiPageDraft
from knowledge_assistant.domain.wiki.entities import WikiPage
from knowledge_assistant.domain.wiki.merger import (
    WikiConflictDraft,
    WikiMergeResult,
    WikiPageMerger,
)


class ConflictPayload(BaseModel):
    existing_statement: str = Field(min_length=1)
    incoming_statement: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class MergePayload(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    summary: str = Field(min_length=1)
    content_markdown: str = Field(min_length=1)
    conflicts: list[ConflictPayload] = Field(default_factory=list)


class OpenRouterWikiPageMerger(WikiPageMerger):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
        timeout_seconds: float = 180.0,
        max_output_tokens: int = 12000,
    ) -> None:
        cleaned_api_key = api_key.strip()
        cleaned_model = model.strip()

        if not cleaned_api_key:
            raise ValueError("OpenRouter API key cannot be empty.")

        if not cleaned_model:
            raise ValueError("OpenRouter model cannot be empty.")

        self._api_key = cleaned_api_key
        self._model = cleaned_model
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._max_output_tokens = max(1000, max_output_tokens)

    async def merge(
        self,
        *,
        existing_page: WikiPage,
        incoming_draft: WikiPageDraft,
        document_title: str,
    ) -> WikiMergeResult:
        response_payload = {
            "model": self._model,
            "temperature": 0.0,
            "max_tokens": self._max_output_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": self._user_prompt(
                        existing_page=existing_page,
                        incoming_draft=incoming_draft,
                        document_title=document_title,
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "wiki_page_merge",
                    "strict": True,
                    "schema": MergePayload.model_json_schema(),
                },
            },
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                self._base_url,
                headers=headers,
                content=json.dumps(
                    response_payload,
                    ensure_ascii=True,
                    separators=(",", ":"),
                ).encode("utf-8"),
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "OpenRouter wiki merge failed: "
                f"{response.status_code} {response.text[:1000]}"
            ) from error

        raw_content = self._extract_content(response.json())
        parsed_payload = self._parse_payload(
            raw_content=raw_content,
            existing_page=existing_page,
        )

        return WikiMergeResult(
            title=parsed_payload.title.strip(),
            summary=parsed_payload.summary.strip(),
            content_markdown=parsed_payload.content_markdown.strip(),
            conflicts=tuple(
                WikiConflictDraft(
                    existing_statement=item.existing_statement.strip(),
                    incoming_statement=item.incoming_statement.strip(),
                    explanation=item.explanation.strip(),
                )
                for item in parsed_payload.conflicts
            ),
        )

    @classmethod
    def _parse_payload(
        cls,
        *,
        raw_content: str,
        existing_page: WikiPage,
    ) -> MergePayload:
        normalized_content = cls._normalize_json_content(raw_content)

        try:
            parsed_json = json.loads(normalized_content)
        except json.JSONDecodeError as error:
            raise ValueError(
                "The LLM returned invalid Wiki merge JSON at "
                f"line {error.lineno}, column {error.colno}."
            ) from error

        payload_data = cls._coerce_payload_shape(
            parsed_json=parsed_json,
            existing_page=existing_page,
        )

        try:
            return MergePayload.model_validate(payload_data)
        except ValidationError as error:
            issues = "; ".join(
                f"{'.'.join(str(part) for part in issue['loc'])}: "
                f"{issue['msg']}"
                for issue in error.errors()[:5]
            )
            raise ValueError(
                "The LLM returned an invalid Wiki merge structure: "
                f"{issues}"
            ) from error

    @staticmethod
    def _coerce_payload_shape(
        *,
        parsed_json: Any,
        existing_page: WikiPage,
    ) -> dict[str, Any]:
        if not isinstance(parsed_json, dict):
            raise ValueError(
                "The LLM returned an invalid Wiki merge structure: "
                "the top-level JSON value must be an object."
            )

        payload: dict[str, Any] = dict(parsed_json)

        for wrapper_key in (
            "merged_page",
            "wiki_page",
            "page",
            "result",
            "data",
        ):
            nested = payload.get(wrapper_key)
            if isinstance(nested, dict):
                payload = dict(nested)
                break

        if not payload.get("content_markdown"):
            for alias in ("content", "markdown", "merged_content"):
                value = payload.get(alias)
                if isinstance(value, str) and value.strip():
                    payload["content_markdown"] = value
                    break

        if not payload.get("title"):
            payload["title"] = existing_page.title

        if not payload.get("summary"):
            existing_summary = existing_page.summary.strip()
            if existing_summary:
                payload["summary"] = existing_summary
            else:
                content_value = payload.get("content_markdown")
                if isinstance(content_value, str) and content_value.strip():
                    payload["summary"] = content_value.strip()[:500]

        conflicts = payload.get("conflicts")
        if conflicts is None:
            payload["conflicts"] = []
        elif isinstance(conflicts, list):
            normalized_conflicts: list[dict[str, Any]] = []

            for item in conflicts:
                if not isinstance(item, dict):
                    continue

                existing_statement = (
                    item.get("existing_statement")
                    or item.get("existing")
                    or item.get("old_statement")
                )
                incoming_statement = (
                    item.get("incoming_statement")
                    or item.get("incoming")
                    or item.get("new_statement")
                )
                explanation = (
                    item.get("explanation")
                    or item.get("reason")
                    or item.get("description")
                )

                if all(
                    isinstance(value, str) and value.strip()
                    for value in (
                        existing_statement,
                        incoming_statement,
                        explanation,
                    )
                ):
                    normalized_conflicts.append(
                        {
                            "existing_statement": existing_statement,
                            "incoming_statement": incoming_statement,
                            "explanation": explanation,
                        }
                    )

            payload["conflicts"] = normalized_conflicts

        return payload

    @staticmethod
    def _normalize_json_content(content: str) -> str:
        normalized = content.strip()

        if normalized.startswith("```"):
            lines = normalized.splitlines()

            if lines and lines[0].strip().lower() in {"```", "```json"}:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            normalized = "\n".join(lines).strip()

        object_start = normalized.find("{")
        object_end = normalized.rfind("}")

        if object_start >= 0 and object_end > object_start:
            normalized = normalized[object_start : object_end + 1]

        return normalized

    @staticmethod
    def _extract_content(response_data: dict[str, Any]) -> str:
        try:
            content = response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError(
                "OpenRouter returned an unexpected Wiki merge response."
            ) from error

        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []

            for part in content:
                if not isinstance(part, dict):
                    continue

                text_value = part.get("text")
                if isinstance(text_value, str):
                    text_parts.append(text_value)

            combined_content = "".join(text_parts).strip()
            if combined_content:
                return combined_content

        raise ValueError("OpenRouter returned an empty Wiki merge response.")

    @staticmethod
    def _system_prompt() -> str:
        return """
You maintain a long-lived internal Wiki from traceable source documents.
Merge the incoming draft into the existing page without deleting valid,
source-supported knowledge. Keep the page concise, structured and neutral.
Do not invent facts. Do not silently choose one side when two sources make
materially incompatible claims. Preserve both claims in the merged article
with cautious wording and return each contradiction in the conflicts array.
Preserve every existing and incoming Markdown citation link whose target starts
with citation:. Do not rename, remove, or invent citation identifiers. Place the
citation link at the end of the factual paragraph it supports. A conflict is a
factual disagreement, not merely a difference in wording or level of detail.
Return valid JSON matching the supplied schema only.
""".strip()

    @staticmethod
    def _user_prompt(
        *,
        existing_page: WikiPage,
        incoming_draft: WikiPageDraft,
        document_title: str,
    ) -> str:
        return f"""
EXISTING WIKI PAGE
Title: {existing_page.title}
Slug: {existing_page.slug}
Summary: {existing_page.summary}
Content:
{existing_page.content_markdown}

INCOMING SOURCE DOCUMENT
{document_title}

INCOMING WIKI DRAFT
Title: {incoming_draft.title}
Slug: {incoming_draft.slug}
Summary: {incoming_draft.summary}
Content:
{incoming_draft.content_markdown}

Produce one merged page. Keep the existing page identity and topic. Report
only genuine factual conflicts in conflicts.
""".strip()
