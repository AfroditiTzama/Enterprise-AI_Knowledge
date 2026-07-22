# Karpathy-inspired Wiki — Core maintenance patch

This patch adds the safe core of an LLM-maintained Wiki:

- true semantic/exact page merging instead of overwriting existing content;
- conflict detection during LLM merge;
- persisted conflict review state (open, resolved, dismissed);
- revision comparison;
- restore of historical revisions as a new revision;
- Wiki UI for conflicts, revision diffs and restore.

## Database migration

Run:

```bash
cd apps/api
source .venv/bin/activate
alembic upgrade head
```

Railway already runs `alembic upgrade head` from the Docker start command.

## Validation

```bash
cd apps/api
source .venv/bin/activate
pytest -q

cd ../web
npm run build
```

## Important behavior

When an incoming draft matches an existing page, OpenRouter now performs an
additional merge request. This improves knowledge preservation and conflict
handling, but increases Wiki compilation latency and token usage.

## Next maintenance milestones

1. owner-wide duplicate-page maintenance and canonical-page selection;
2. automatic link repair and orphan-page detection;
3. large-page split proposals and safe merge proposals;
4. stale/unsupported-claim quality checks;
5. scheduled autonomous maintenance after manual review mode is stable.
