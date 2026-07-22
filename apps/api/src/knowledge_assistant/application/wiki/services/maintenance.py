import hashlib
import re
from difflib import SequenceMatcher

from knowledge_assistant.application.wiki.services.quality import (
    calculate_wiki_quality,
)
from knowledge_assistant.domain.wiki.entities import (
    WikiMaintenanceIssueType,
    WikiMaintenanceSuggestionDraft,
    WikiPageDetails,
)


_CITATION_PATTERN = re.compile(r"\]\(citation:([^)]+)\)", re.IGNORECASE)
_INTERNAL_WIKI_PATTERN = re.compile(
    r"\]\((?:/wiki\?slug=|wiki:)([^)]+)\)",
    re.IGNORECASE,
)


def _fingerprint(
    issue_type: WikiMaintenanceIssueType,
    page_ids: tuple[str, ...],
    marker: str,
) -> str:
    raw_value = "|".join(
        [issue_type.value, *sorted(page_ids), marker]
    )
    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()


def _normalized_words(value: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9]+", value.lower())
        if len(word) > 2
    }


def _duplicate_score(first: WikiPageDetails, second: WikiPageDetails) -> float:
    first_text = f"{first.page.title} {first.page.summary}".strip().lower()
    second_text = f"{second.page.title} {second.page.summary}".strip().lower()
    sequence_score = SequenceMatcher(None, first_text, second_text).ratio()

    first_words = _normalized_words(first_text)
    second_words = _normalized_words(second_text)
    union = first_words | second_words
    token_score = (
        len(first_words & second_words) / len(union)
        if union
        else 0.0
    )

    return max(sequence_score, token_score)


def detect_maintenance_suggestions(
    details_list: list[WikiPageDetails],
) -> list[WikiMaintenanceSuggestionDraft]:
    suggestions: list[WikiMaintenanceSuggestionDraft] = []
    known_slugs = {details.page.slug for details in details_list}

    for details in details_list:
        page = details.page
        quality = calculate_wiki_quality(details)
        page_id = str(page.id)
        word_count = len(re.findall(r"\b\w+\b", page.content_markdown))

        if quality.connections_count == 0:
            suggestions.append(
                WikiMaintenanceSuggestionDraft(
                    issue_type=WikiMaintenanceIssueType.ORPHAN,
                    fingerprint=_fingerprint(
                        WikiMaintenanceIssueType.ORPHAN,
                        (page_id,),
                        page.slug,
                    ),
                    title=f"Connect orphan page: {page.title}",
                    description=(
                        "This page has no related pages or backlinks. "
                        "Review whether it should be linked, merged, or kept standalone."
                    ),
                    page_ids=(page.id,),
                    metadata={
                        "slug": page.slug,
                        "connections": 0,
                    },
                    confidence=1.0,
                )
            )

        if word_count > 1200:
            suggestions.append(
                WikiMaintenanceSuggestionDraft(
                    issue_type=WikiMaintenanceIssueType.OVERSIZED,
                    fingerprint=_fingerprint(
                        WikiMaintenanceIssueType.OVERSIZED,
                        (page_id,),
                        str(word_count),
                    ),
                    title=f"Split large page: {page.title}",
                    description=(
                        "The page is large enough to reduce scanability and retrieval precision. "
                        "Preview a split into smaller atomic topics before applying it."
                    ),
                    page_ids=(page.id,),
                    metadata={"word_count": word_count, "slug": page.slug},
                    confidence=min(1.0, word_count / 2000),
                )
            )
        elif word_count < 80:
            suggestions.append(
                WikiMaintenanceSuggestionDraft(
                    issue_type=WikiMaintenanceIssueType.UNDERSIZED,
                    fingerprint=_fingerprint(
                        WikiMaintenanceIssueType.UNDERSIZED,
                        (page_id,),
                        str(word_count),
                    ),
                    title=f"Review small page: {page.title}",
                    description=(
                        "This page contains very little standalone knowledge. "
                        "Consider enriching it or merging it into a closely related page."
                    ),
                    page_ids=(page.id,),
                    metadata={"word_count": word_count, "slug": page.slug},
                    confidence=max(0.55, 1.0 - (word_count / 100)),
                )
            )

        if quality.unsupported_claims > 0:
            suggestions.append(
                WikiMaintenanceSuggestionDraft(
                    issue_type=WikiMaintenanceIssueType.UNSUPPORTED_CLAIMS,
                    fingerprint=_fingerprint(
                        WikiMaintenanceIssueType.UNSUPPORTED_CLAIMS,
                        (page_id,),
                        str(quality.unsupported_claims),
                    ),
                    title=f"Review unsupported content: {page.title}",
                    description=(
                        f"{quality.unsupported_claims} content block(s) do not include "
                        "claim-level source citations."
                    ),
                    page_ids=(page.id,),
                    metadata={
                        "unsupported_claims": quality.unsupported_claims,
                        "source_coverage": quality.source_coverage,
                        "slug": page.slug,
                    },
                    confidence=0.95,
                )
            )

        claim_keys = {
            claim.claim_key.lower()
            for claim in details.claim_citations
        }
        cited_keys = {
            match.group(1).strip().lower()
            for match in _CITATION_PATTERN.finditer(page.content_markdown)
        }
        broken_citations = sorted(cited_keys - claim_keys)

        linked_slugs = {
            match.group(1).strip().lower()
            for match in _INTERNAL_WIKI_PATTERN.finditer(page.content_markdown)
        }
        broken_slugs = sorted(linked_slugs - known_slugs)

        if broken_citations or broken_slugs:
            suggestions.append(
                WikiMaintenanceSuggestionDraft(
                    issue_type=WikiMaintenanceIssueType.BROKEN_LINK,
                    fingerprint=_fingerprint(
                        WikiMaintenanceIssueType.BROKEN_LINK,
                        (page_id,),
                        ",".join([*broken_citations, *broken_slugs]),
                    ),
                    title=f"Repair broken references: {page.title}",
                    description=(
                        "The page contains citation or Wiki links that no longer resolve."
                    ),
                    page_ids=(page.id,),
                    metadata={
                        "broken_citations": broken_citations,
                        "broken_wiki_slugs": broken_slugs,
                        "slug": page.slug,
                    },
                    confidence=1.0,
                )
            )

    for index, first in enumerate(details_list):
        for second in details_list[index + 1 :]:
            score = _duplicate_score(first, second)
            if score < 0.86:
                continue

            page_ids = tuple(
                sorted(
                    (str(first.page.id), str(second.page.id))
                )
            )
            suggestions.append(
                WikiMaintenanceSuggestionDraft(
                    issue_type=WikiMaintenanceIssueType.DUPLICATE,
                    fingerprint=_fingerprint(
                        WikiMaintenanceIssueType.DUPLICATE,
                        page_ids,
                        f"{score:.3f}",
                    ),
                    title=(
                        f"Review possible duplicate: {first.page.title} / "
                        f"{second.page.title}"
                    ),
                    description=(
                        "These pages are highly similar. Preview both pages before "
                        "approving a future semantic merge."
                    ),
                    page_ids=(first.page.id, second.page.id),
                    metadata={
                        "first_slug": first.page.slug,
                        "second_slug": second.page.slug,
                        "similarity": round(score, 3),
                    },
                    confidence=round(score, 3),
                )
            )

    return suggestions
