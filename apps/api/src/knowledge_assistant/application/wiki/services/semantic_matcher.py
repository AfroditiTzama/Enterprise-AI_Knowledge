import math

from knowledge_assistant.domain.embeddings.service import (
    EmbeddingService,
)
from knowledge_assistant.domain.wiki.compiler import (
    WikiPageDraft,
)
from knowledge_assistant.domain.wiki.entities import WikiPage
from knowledge_assistant.domain.wiki.matcher import (
    WikiMatchDecision,
    WikiMatchResult,
    WikiSemanticMatcher,
)


class EmbeddingWikiSemanticMatcher(
    WikiSemanticMatcher
):
    def __init__(
        self,
        *,
        embedding_service: EmbeddingService,
        candidate_threshold: float = 0.82,
    ) -> None:
        if not 0.0 <= candidate_threshold <= 1.0:
            raise ValueError(
                "Candidate threshold must be between 0 and 1."
            )

        self._embedding_service = embedding_service
        self._candidate_threshold = candidate_threshold

    async def match(
        self,
        *,
        drafts: tuple[WikiPageDraft, ...],
        existing_pages: tuple[WikiPage, ...],
    ) -> tuple[WikiMatchResult, ...]:
        if not drafts:
            return ()

        existing_by_slug = {
            page.slug.strip().lower(): page
            for page in existing_pages
        }

        results_by_slug: dict[
            str,
            WikiMatchResult,
        ] = {}

        unresolved_drafts: list[WikiPageDraft] = []

        for draft in drafts:
            draft_slug = draft.slug.strip().lower()
            exact_page = existing_by_slug.get(
                draft_slug
            )

            if exact_page is not None:
                results_by_slug[draft_slug] = (
                    WikiMatchResult(
                        draft_slug=draft_slug,
                        decision=(
                            WikiMatchDecision.EXACT_MATCH
                        ),
                        matched_page_id=exact_page.id,
                        matched_page_slug=exact_page.slug,
                        score=1.0,
                    )
                )
            else:
                unresolved_drafts.append(draft)

        if not unresolved_drafts:
            return tuple(
                results_by_slug[
                    draft.slug.strip().lower()
                ]
                for draft in drafts
            )

        if not existing_pages:
            for draft in unresolved_drafts:
                draft_slug = draft.slug.strip().lower()

                results_by_slug[draft_slug] = (
                    WikiMatchResult(
                        draft_slug=draft_slug,
                        decision=WikiMatchDecision.CREATE,
                        matched_page_id=None,
                        matched_page_slug=None,
                        score=None,
                    )
                )

            return tuple(
                results_by_slug[
                    draft.slug.strip().lower()
                ]
                for draft in drafts
            )

        draft_texts = [
            self._format_draft(draft)
            for draft in unresolved_drafts
        ]

        page_texts = [
            self._format_page(page)
            for page in existing_pages
        ]

        all_embeddings = (
            await self._embedding_service.embed_documents(
                draft_texts + page_texts
            )
        )

        expected_count = (
            len(draft_texts) + len(page_texts)
        )

        if len(all_embeddings) != expected_count:
            raise ValueError(
                "Wiki semantic embedding count mismatch."
            )

        draft_embeddings = all_embeddings[
            :len(draft_texts)
        ]

        page_embeddings = all_embeddings[
            len(draft_texts):
        ]

        for draft, draft_embedding in zip(
            unresolved_drafts,
            draft_embeddings,
            strict=True,
        ):
            best_page: WikiPage | None = None
            best_score = -1.0

            for page, page_embedding in zip(
                existing_pages,
                page_embeddings,
                strict=True,
            ):
                score = self._cosine_similarity(
                    draft_embedding,
                    page_embedding,
                )

                if score > best_score:
                    best_page = page
                    best_score = score

            draft_slug = draft.slug.strip().lower()

            if (
                best_page is not None
                and best_score
                >= self._candidate_threshold
            ):
                results_by_slug[draft_slug] = (
                    WikiMatchResult(
                        draft_slug=draft_slug,
                        decision=(
                            WikiMatchDecision
                            .SEMANTIC_CANDIDATE
                        ),
                        matched_page_id=best_page.id,
                        matched_page_slug=best_page.slug,
                        score=best_score,
                    )
                )
            else:
                results_by_slug[draft_slug] = (
                    WikiMatchResult(
                        draft_slug=draft_slug,
                        decision=WikiMatchDecision.CREATE,
                        matched_page_id=None,
                        matched_page_slug=None,
                        score=(
                            best_score
                            if best_score >= 0
                            else None
                        ),
                    )
                )

        return tuple(
            results_by_slug[
                draft.slug.strip().lower()
            ]
            for draft in drafts
        )

    @staticmethod
    def _format_draft(
        draft: WikiPageDraft,
    ) -> str:
        return "\n\n".join(
            part.strip()
            for part in (
                draft.title,
                draft.summary,
            )
            if part.strip()
        )

    @staticmethod
    def _format_page(
        page: WikiPage,
    ) -> str:
        return "\n\n".join(
            part.strip()
            for part in (
                page.title,
                page.summary,
            )
            if part.strip()
        )

    @staticmethod
    def _cosine_similarity(
        first: list[float],
        second: list[float],
    ) -> float:
        if len(first) != len(second):
            raise ValueError(
                "Embedding dimensions do not match."
            )

        dot_product = sum(
            left * right
            for left, right in zip(
                first,
                second,
                strict=True,
            )
        )

        first_norm = math.sqrt(
            sum(value * value for value in first)
        )

        second_norm = math.sqrt(
            sum(value * value for value in second)
        )

        denominator = first_norm * second_norm

        if denominator == 0:
            return 0.0

        return dot_product / denominator
