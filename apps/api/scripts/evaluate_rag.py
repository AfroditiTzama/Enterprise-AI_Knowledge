"""Evaluate retrieval, citations and groundedness against the running API.

JSONL case example:
{"question":"What is X?","expected_titles":["source.pdf"],"k":5}

Environment:
EVAL_API_BASE_URL=http://127.0.0.1:8000
EVAL_EMAIL=user@example.com
EVAL_PASSWORD=...
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx

from knowledge_assistant.domain.evaluation.metrics import (
    answer_metrics,
    retrieval_metrics,
)


async def _source_text(
    client: httpx.AsyncClient,
    source: dict[str, Any],
) -> str:
    source_type = str(source.get("source_type", ""))
    slug = source.get("slug")
    if source_type == "wiki" and slug:
        response = await client.get(f"/wiki/pages/{slug}")
        if response.is_success:
            return str(response.json().get("content_markdown", ""))
        return ""

    document_id = source.get("document_id")
    chunk_index = source.get("chunk_index")
    if document_id and chunk_index is not None:
        response = await client.get(
            f"/documents/{document_id}/chunks/{chunk_index}"
        )
        if response.is_success:
            return str(response.json().get("text", ""))
    return ""


async def run(dataset_path: Path, output_path: Path) -> None:
    base_url = (
        os.getenv("EVAL_API_BASE_URL")
        or os.getenv("EVAL_BASE_URL")
        or "http://127.0.0.1:8000"
    ).rstrip("/")
    email = os.environ["EVAL_EMAIL"]
    password = os.environ["EVAL_PASSWORD"]
    cases = [
        json.loads(line)
        for line in dataset_path.read_text().splitlines()
        if line.strip()
    ]

    results: list[dict[str, object]] = []
    async with httpx.AsyncClient(base_url=base_url, timeout=180) as client:
        login = await client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        login.raise_for_status()
        csrf_token = login.json()["csrf_token"]

        for case in cases:
            response = await client.post(
                "/chat/ask",
                headers={"x-csrf-token": csrf_token},
                json={
                    "question": case["question"],
                    "source_scope": case.get("source_scope", "all"),
                    "document_ids": case.get("document_ids", []),
                    "content_types": case.get("content_types", []),
                    "max_sources": case.get("k", 7),
                },
            )
            response.raise_for_status()
            payload = response.json()
            sources = payload.get("sources", [])
            retrieved_titles = [str(item.get("title", "")) for item in sources]
            expected_titles = set(case.get("expected_titles", []))
            retrieval = retrieval_metrics(
                retrieved_ids=retrieved_titles,
                expected_ids=expected_titles,
                k=int(case.get("k", 7)),
            )
            source_texts = [
                text
                for text in await asyncio.gather(
                    *(_source_text(client, item) for item in sources)
                )
                if text
            ]
            answer = answer_metrics(
                answer=str(payload.get("answer_markdown", "")),
                available_source_ids={
                    str(item.get("source_id", "")) for item in sources
                },
                source_texts=source_texts,
                question=str(case["question"]),
            )
            results.append(
                {
                    "question": case["question"],
                    "precision_at_k": retrieval.precision_at_k,
                    "recall_at_k": retrieval.recall_at_k,
                    "mrr": retrieval.reciprocal_rank,
                    "citation_correctness": answer.citation_correctness,
                    "citation_coverage": answer.citation_coverage,
                    "answer_relevance": answer.answer_relevance,
                    "groundedness": answer.groundedness,
                    "retrieval_mode": payload.get("retrieval_mode"),
                    "estimated_cost_usd": payload.get(
                        "estimated_cost_usd", 0
                    ),
                    "cache_hit": payload.get("cache_hit", False),
                }
            )

    numeric_keys = [
        "precision_at_k",
        "recall_at_k",
        "mrr",
        "citation_correctness",
        "citation_coverage",
        "answer_relevance",
        "groundedness",
        "estimated_cost_usd",
    ]
    summary = {
        key: sum(float(item[key]) for item in results) / max(len(results), 1)
        for key in numeric_keys
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {"cases": results, "summary": summary},
            indent=2,
            ensure_ascii=False,
        )
    )
    print(json.dumps(summary, indent=2))


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _arguments()
    asyncio.run(run(arguments.dataset, arguments.output))
