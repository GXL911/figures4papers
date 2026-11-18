# Reference Atlas — Development Benchmark Protocol

## Current fixture

The first v0.3 branch contains 16 paper records, 16 figure-level metadata records, eight search queries with hand-authored graded relevance judgments, and five independent taxonomy facets.

All 16 figure records are marked provisional. The records are metadata-only and have no local image assets.

## Metrics

- MRR@k: reciprocal rank of the first relevant result.
- Recall@k: fraction of known relevant results retrieved in the top k.
- nDCG@k: graded ranking quality with gain 2^rel - 1 and logarithmic rank discount.

The evaluator reports per-query metrics and macro averages. Averages do not hide per-domain failures once the dataset grows.

## Reproducibility

Run:

    python -m figures4papers.retrieval_eval --k 5 --out reference-eval.json

The qrels are stored in data/reference-atlas/queries.json. Do not change qrels and retrieval weights in the same experiment without recording the change. The current qrels were authored for smoke testing and have not been independently judged; their scores are not a general benchmark claim.

## Next benchmark milestone

Before comparing CLIP or tuning field boosts:
1. visually inspect the exact figure in each original paper PDF;
2. verify figure number, caption, page and panel boundaries;
3. promote only verified records to curated;
4. expand to 30–50 references with balanced visual forms and domains;
5. write at least 30–50 natural-language queries, including queries that deliberately distinguish similar-looking architectures;
6. have two reviewers independently judge relevance on a 0–3 scale;
7. adjudicate disagreements and report agreement;
8. freeze a development/test split by paper or topic to reduce leakage;
9. compare BM25, structural facets, semantic retrieval and RRF ablations;
10. report MRR, nDCG, Recall and error cases by figure role and visual form.

## Human review rubric

Score each candidate separately on scientific-topic relevance, figure-role relevance, visual-form relevance, layout transferability, and clarity/publication suitability.

A candidate can be semantically relevant but visually unsuitable. Preserve these dimensions separately rather than hiding them in one relevance score.
