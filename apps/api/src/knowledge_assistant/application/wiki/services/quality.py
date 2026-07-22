import re
from datetime import datetime, timezone

from knowledge_assistant.domain.wiki.entities import (
    WikiConflictStatus,
    WikiPageDetails,
    WikiQualityScore,
)


_CITATION_PATTERN = re.compile(r"\]\(citation:([^)]+)\)", re.IGNORECASE)


def _claim_blocks(content_markdown: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_code_block = False

    for raw_line in content_markdown.splitlines():
        line = raw_line.strip()

        if line.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        if not line:
            if current:
                blocks.append(" ".join(current))
                current = []
            continue

        if line.startswith("#"):
            if current:
                blocks.append(" ".join(current))
                current = []
            continue

        if line.startswith("|") and line.endswith("|"):
            continue

        cleaned = re.sub(r"^[-*+]\s+", "", line)
        cleaned = re.sub(r"^\d+[.)]\s+", "", cleaned)
        current.append(cleaned)

    if current:
        blocks.append(" ".join(current))

    return [
        block
        for block in blocks
        if len(re.findall(r"\b\w+\b", block)) >= 8
    ]


def calculate_wiki_quality(details: WikiPageDetails) -> WikiQualityScore:
    blocks = _claim_blocks(details.page.content_markdown)
    known_claim_keys = {
        claim.claim_key.strip().lower()
        for claim in details.claim_citations
    }

    cited_blocks = [
        block
        for block in blocks
        if any(
            match.group(1).strip().lower() in known_claim_keys
            for match in _CITATION_PATTERN.finditer(block)
        )
    ]

    supported_claims = len(cited_blocks)
    unsupported_claims = max(0, len(blocks) - supported_claims)

    if blocks:
        source_coverage = round(100 * supported_claims / len(blocks))
    elif details.sources:
        source_coverage = 100
    else:
        source_coverage = 0

    updated_at = details.page.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    age_days = max(
        0,
        (datetime.now(timezone.utc) - updated_at).days,
    )

    if age_days <= 90:
        freshness = 100
    elif age_days <= 180:
        freshness = 85
    elif age_days <= 365:
        freshness = 65
    else:
        freshness = 40

    open_conflicts = sum(
        conflict.status == WikiConflictStatus.OPEN
        for conflict in details.conflicts
    )
    consistency = max(20, 100 - (open_conflicts * 25))

    connections_count = (
        len(details.related_pages)
        + len(details.backlinks)
    )
    if connections_count == 0:
        connectivity = 20
    elif connections_count == 1:
        connectivity = 60
    elif connections_count == 2:
        connectivity = 80
    else:
        connectivity = 100

    overall = round(
        (source_coverage * 0.4)
        + (freshness * 0.2)
        + (consistency * 0.25)
        + (connectivity * 0.15)
    )

    issues: list[str] = []

    if not details.sources:
        issues.append("No active source references")

    if unsupported_claims:
        issues.append(
            f"{unsupported_claims} unsupported content block"
            + ("s" if unsupported_claims != 1 else "")
        )

    if open_conflicts:
        issues.append(
            f"{open_conflicts} open conflict"
            + ("s" if open_conflicts != 1 else "")
        )

    if connections_count == 0:
        issues.append("Orphan page with no Wiki connections")

    if freshness < 65:
        issues.append("Content may be stale")

    return WikiQualityScore(
        source_coverage=source_coverage,
        freshness=freshness,
        consistency=consistency,
        connectivity=connectivity,
        overall=overall,
        supported_claims=supported_claims,
        unsupported_claims=unsupported_claims,
        open_conflicts=open_conflicts,
        connections_count=connections_count,
        issues=tuple(issues),
    )
