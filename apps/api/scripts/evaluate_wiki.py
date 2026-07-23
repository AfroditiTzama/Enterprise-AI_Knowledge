"""Score offline Wiki conflict, duplicate and merge predictions.

JSONL case example:
{"conflict_expected":"OPEN","conflict_predicted":"OPEN",
 "duplicate_expected":"MATCH","duplicate_predicted":"MATCH",
 "reference_merge":"supported reference text",
 "candidate_merge":"supported candidate text"}
"""

import argparse
import json
from pathlib import Path

from knowledge_assistant.domain.evaluation.metrics import (
    classification_accuracy,
    token_similarity,
)


def run(dataset: Path, output: Path) -> None:
    cases = [
        json.loads(line)
        for line in dataset.read_text().splitlines()
        if line.strip()
    ]
    conflict_expected = [str(case["conflict_expected"]) for case in cases]
    conflict_predicted = [str(case["conflict_predicted"]) for case in cases]
    duplicate_expected = [str(case["duplicate_expected"]) for case in cases]
    duplicate_predicted = [str(case["duplicate_predicted"]) for case in cases]
    merge_scores = [
        token_similarity(
            str(case.get("reference_merge", "")),
            str(case.get("candidate_merge", "")),
        )
        for case in cases
    ]
    report = {
        "cases": len(cases),
        "conflict_detection_accuracy": classification_accuracy(
            conflict_expected, conflict_predicted
        ),
        "duplicate_detection_accuracy": classification_accuracy(
            duplicate_expected, duplicate_predicted
        ),
        "wiki_merge_token_similarity": (
            sum(merge_scores) / max(len(merge_scores), 1)
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2))


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _arguments()
    run(arguments.dataset, arguments.output)
