from uuid import UUID

from knowledge_assistant.application.wiki.services.maintenance import (
    detect_maintenance_suggestions,
)
from knowledge_assistant.application.wiki.services.quality import (
    calculate_wiki_quality,
)
from knowledge_assistant.domain.wiki.entities import (
    WikiMaintenanceSuggestion,
    WikiPageDetails,
)
from knowledge_assistant.domain.wiki.repository import WikiRepository


class ScanWikiMaintenanceCommand:
    def __init__(self, repository: WikiRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        owner_id: UUID,
    ) -> list[WikiMaintenanceSuggestion]:
        pages = await self._repository.list_by_owner_id(owner_id)
        details_list = []

        for page in pages:
            details = await self._repository.get_details_by_slug(
                owner_id=owner_id,
                slug=page.slug,
            )
            if details is None:
                continue

            details = WikiPageDetails(
                page=details.page,
                sources=details.sources,
                related_pages=details.related_pages,
                backlinks=details.backlinks,
                conflicts=details.conflicts,
                claim_citations=details.claim_citations,
                quality=calculate_wiki_quality(details),
            )
            details_list.append(details)

        drafts = detect_maintenance_suggestions(details_list)
        return await self._repository.sync_maintenance_suggestions(
            owner_id=owner_id,
            suggestions=drafts,
        )
