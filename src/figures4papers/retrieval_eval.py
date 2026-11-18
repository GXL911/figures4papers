"""Small, explicit retrieval benchmark utilities for the reference atlas."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .reference_atlas import ReferenceAtlas, _default_atlas_dir


def reciprocal_rank(relevance: Sequence[int], k: int) -> float:
    for rank, grade in enumerate(relevance[:k], start=1):
        if grade > 0:
            return 1.0 / rank
    return 0.0


def recall_at_k(relevance: Sequence[int], total_relevant: int, k: int) -> float:
    if total_relevant <= 0:
        return 0.0
    return sum(grade > 0 for grade in relevance[:k]) / total_relevant


def ndcg_at_k(relevance: Sequence[int], ideal_grades: Sequence[int], k: int) -> float:
    def dcg(grades: Sequence[int]) -> float:
        return sum((2**grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(grades[:k], start=1))
    ideal = dcg(sorted(ideal_grades, reverse=True))
    return dcg(relevance) / ideal if ideal > 0 else 0.0


def evaluate_queries(
    atlas: ReferenceAtlas,
    queries: Sequence[Mapping[str, Any]],
    *,
    k: int = 5,
) -> dict[str, Any]:
    if k < 1:
        raise ValueError("k must be positive.")
    per_query = []
    for item in queries:
        qid = str(item["query_id"])
        hits = atlas.search(
            str(item["query"]),
            limit=k,
            filters=item.get("filters"),
            facets=item.get("facets"),
        )
        qrels = {str(key): int(value) for key, value in item["qrels"].items()}
        ranked_grades = [qrels.get(hit.figure.figure_id, 0) for hit in hits]
        total_relevant = sum(grade > 0 for grade in qrels.values())
        per_query.append({
            "query_id": qid,
            "retrieved_ids": [hit.figure.figure_id for hit in hits],
            f"mrr@{k}": reciprocal_rank(ranked_grades, k),
            f"recall@{k}": recall_at_k(ranked_grades, total_relevant, k),
            f"ndcg@{k}": ndcg_at_k(ranked_grades, list(qrels.values()), k),
            "relevant_count": total_relevant,
        })
    metrics = [f"mrr@{k}", f"recall@{k}", f"ndcg@{k}"]
    macro = {
        metric: sum(row[metric] for row in per_query) / len(per_query) if per_query else 0.0
        for metric in metrics
    }
    return {
        "benchmark_version": "0.1",
        "k": k,
        "query_count": len(per_query),
        "macro_average": macro,
        "queries": per_query,
        "interpretation": (
            "Development-set diagnostics only. Qrels are hand-curated for a small seed atlas; "
            "scores are not evidence of general retrieval quality."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate reference-atlas retrieval against hand-curated qrels.")
    parser.add_argument("--atlas", type=Path, default=_default_atlas_dir())
    parser.add_argument("--queries", type=Path, default=Path("data/reference-atlas/queries.json"))
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    atlas = ReferenceAtlas.from_directory(args.atlas)
    queries = json.loads(args.queries.read_text(encoding="utf-8"))
    report = evaluate_queries(atlas, queries, k=args.k)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
