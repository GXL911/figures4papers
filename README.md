# Research Figure Making — v0.3 foundations

This GXL911 fork extends the original figures4papers case-study repository. It preserves the original plotting scripts and the v0.1/v0.2 work while adding a metadata-first reference atlas, hybrid retrieval foundations, versioned design/scene contracts, and an editable draw.io export path.

## v0.3 scope and implementation status

v0.3 is being developed on feature/research-figure-making-v0.3, based on the v0.2 branch. This is a foundation release, not a claim that the complete AI figure-design system is finished.

| Capability | Status in this branch |
|---|---|
| Reference Atlas metadata model | Implemented |
| Orthogonal Pattern Taxonomy | Implemented |
| Seed atlas | 16 provisional figure records across 16 papers |
| Fielded BM25 | Implemented |
| Hard facet filters and soft structural ranking | Implemented |
| RRF fusion | Implemented |
| CLIP / semantic embedding runtime | Adapter hook only; not bundled |
| Retrieval qrels and metrics | 8-query development set implemented |
| Design Brief JSON Schema and validator | Implemented |
| Scene Graph JSON Schema and validator | Implemented |
| Design Brief → Scene Graph content traceability | Implemented |
| Manual deterministic SVG scene rendering | Implemented |
| Editable draw.io XML export | Implemented for manual-layout box/ellipse scenes |
| ELK automatic layout | Contract/roadmap only; not implemented |
| PPTX native-shape export | Roadmap; not implemented |
| Full visual QA / graph-based benchmark | Roadmap; current QA remains partial |

All seed figure entries are metadata-only and marked provisional. No third-party paper figure binaries are copied into the atlas. A curator must inspect the original PDF and verify the figure locator, caption interpretation, and rights before an entry is promoted to curated.

## Quick start

Python 3.10 or later:

    python -m pip install -e ".[dev,illustration]"
    python -m pytest -q

Search the reference atlas:

    figures4papers-reference --query "selective state space hardware-aware scan" --limit 5

Evaluate the small, hand-curated development qrels:

    python -m figures4papers.retrieval_eval --k 5 --out /tmp/reference-retrieval-eval.json

Render the sample hybrid-memory scene to SVG and draw.io:

    python tools/render_scene.py examples/hybrid_memory_scene.json --brief examples/hybrid_memory_design_brief.json --out /tmp/hybrid-memory

The retrieval qrels are development fixtures, not an independently judged benchmark. Their scores must not be interpreted as general retrieval-quality claims.

## Architecture

The v0.3 design separates five concerns:

1. Scientific Understanding: research question, claims, content blocks, evidence, limitations.
2. Reference Intelligence: metadata atlas, fielded BM25, structured facets, optional image-text embeddings, rank fusion.
3. Figure Design Intelligence: versioned Design Brief and a renderer-neutral Scene Graph.
4. Rendering: existing Matplotlib, DiagramCanvas and FigureComposer, plus format-specific adapters.
5. Scientific & Visual QA: numerical/provenance checks, graph integrity, geometry, typography, contrast, and human review.

LLMs may propose a Design Brief and Scene Graph. They do not directly paint final pixels or invent experimental data. Rendering remains deterministic and data-driven.

## Key files

- data/reference-atlas/papers.jsonl: bibliographic records.
- data/reference-atlas/figures.jsonl: figure-level metadata and design annotations.
- data/reference-atlas/taxonomy.json: independent scientific-intent, figure-role, visual-form and layout facets.
- data/reference-atlas/queries.json: hand-curated development queries and qrels.
- src/figures4papers/reference_atlas.py: atlas validation, fielded BM25, facet search and RRF.
- src/figures4papers/retrieval_eval.py: MRR, Recall@k and nDCG@k.
- schemas/design-brief.schema.json: semantic design contract.
- schemas/scene.schema.json: renderer-neutral scene graph contract.
- src/figures4papers/design_contracts.py: runtime validation, brief-to-scene traceability and deterministic SVG adapter.
- src/figures4papers/drawio_export.py: native mxCell export for editable diagrams.
- docs/V0.3_ARCHITECTURE.md: architecture, decisions, limits and roadmap.
- docs/RESEARCH_REFERENCES.md: primary papers and official technical documentation.

## Existing v0.1/v0.2 functionality

The earlier phases remain the foundation: publication-oriented Matplotlib charts, numeric/statistical validation, provenance manifests, physical-size-aware design tokens, SVG-native DiagramCanvas, and FigureComposer. See the existing documentation and benchmark examples.

The upstream license and artwork rights remain unchanged. This fork does not relicense original material. Third-party paper images are not redistributed by the v0.3 metadata atlas.
