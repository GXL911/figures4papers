# v0.3 Research References and Technical Sources

**Research checked:** 18 November 2026

## A. Multimodal and diagram retrieval

### 1. CLIP
Radford et al. (2021), *Learning Transferable Visual Models From Natural Language Supervision*.
- Paper: https://arxiv.org/abs/2103.00020
- Official implementation: https://github.com/openai/CLIP
- Relevant implementation: encode_image, encode_text, normalized image/text features and cosine similarity.
- Design decision: CLIP is an optional semantic retrieval signal. Its image-text contrastive objective does not establish diagram topology or scientific correctness.

### 2. DiagramEval
Liang & You (2025), *DiagramEval: Evaluating LLM-Generated Diagrams via Graphs*, EMNLP 2025.
- Proceedings PDF: https://aclanthology.org/2025.emnlp-main.640.pdf
- Code: https://github.com/ulab-uiuc/diagram-eval
- Relevant idea: represent diagram text elements as graph nodes and connections as directed edges; assess Node Alignment and Path Alignment.
- Design decision: future visual QA should compare scene semantics and topology, not rely only on image similarity or CLIPScore.

### 3. BM25
Robertson & Walker (1994), *Some Simple Effective Approximations to the 2-Poisson Model for Probabilistic Weighted Retrieval*.
- Original paper: https://www.staff.city.ac.uk/~sbrp622/papers/dublin/dublin.html
- Design decision: use a transparent fielded BM25 baseline with explicit field boosts and length normalization.

### 4. Reciprocal Rank Fusion
Cormack, Clarke & Buettcher (2009), *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods*, SIGIR 2009.
- Original author-hosted PDF: https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf
- DOI: https://doi.org/10.1145/1571941.1572114
- Google Research record: https://research.google/pubs/reciprocal-rank-fusion-outperforms-condorcet-and-individual-rank-learning-methods/
- Design decision: fuse independent lexical, structured and optional semantic rankings by rank rather than summing incomparable raw scores.

## B. Scientific figure and PDF extraction

### 5. SciCap
Hsu, Giles & Huang (2021), *SciCAP: Generating Captions for Scientific Figures*, Findings of EMNLP 2021.
- Paper: https://aclanthology.org/2021.findings-emnlp.277/
- PDF: https://aclanthology.org/2021.findings-emnlp.277.pdf
- Relevant findings: figure-type classification, subfigure identification and caption normalization are separate processing steps; the dataset contains more than two million figures from over 290,000 CS arXiv papers.
- Design decision: store figure type and panel/subfigure metadata separately; do not assume automatic extraction is error-free.

### 6. PubLayNet
Zhong et al. (2019), *PubLayNet: Largest Dataset Ever for Document Layout Analysis*.
- DOI: https://doi.org/10.1109/ICDAR.2019.00166
- Dataset: https://github.com/ibm-aur-nlp/PubLayNet
- Design decision: use document-layout research as background for page-region extraction, not as a substitute for scientific figure semantics.

### 7. DocLayNet
Pfitzmann et al. (2022), *DocLayNet: A Large Human-Annotated Dataset for Document-Layout Analysis*.
- Paper: https://arxiv.org/abs/2206.01062
- DOI: https://doi.org/10.1145/3534678.3539043
- Relevant contribution: 80,863 manually annotated pages with 11 document-layout classes and a subset with multiple annotations.
- Design decision: layout models need diversity and human-verified labels; page-layout classes and figure-design patterns are different taxonomies.

### 8. PyMuPDF
Official Page API: https://pymupdf.readthedocs.io/en/latest/page.html
- Page.get_text("dict") can expose text and image block metadata.
- Page.get_drawings() exposes vector drawing instructions such as lines, rectangles and curves.
- Design decision: begin PDF extraction with text blocks, vector geometry and caption proximity before introducing a trained document-vision model.

## C. Graph layout and editable formats

### 9. Eclipse Layout Kernel (ELK)
Official site: https://eclipse.dev/elk/
- Layered algorithm: https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html
- JSON graph format: https://eclipse.dev/elk/documentation/tooldevelopers/graphdatastructure/jsonformat.html
- Relevant capabilities: layered node placement, edge-crossing reduction, ports, orthogonal routing, compound graphs and edge labels.
- Important boundary: ELK computes layout; it does not render the final diagram.
- Design decision: keep a renderer-neutral Scene Graph and connect ELK through a layout adapter.

### 10. W3C SVG 2
W3C Candidate Recommendation Snapshot, 6 October 2026.
- Specification: https://www.w3.org/TR/SVG/
- Design decision: preserve vector geometry, text semantics, titles/descriptions and accessibility metadata. The cited 2026 snapshot is a Candidate Recommendation, not a claim that every editor supports every feature.

### 11. draw.io XML
Official documentation: https://www.drawio.com/docs/reference/diagram-generation/
- File format: mxfile → diagram → mxGraphModel → root → mxCell.
- Vertices use vertex="1" and edges use edge="1" with source/target references.
- Validation schema: https://github.com/jgraph/drawio-tools/blob/master/etc/mxfile.xsd
- Design decision: export native nodes and connectors, not a flattened image. The current adapter implements only a conservative manual-layout subset.

### 12. python-pptx
Official Shape API: https://python-pptx.readthedocs.io/en/latest/api/shapes.html
- Supports native shapes, text boxes and pictures.
- Design decision: future PPTX export should map semantic scene objects to editable PowerPoint shapes/text/connectors. Embedding an SVG or PNG alone is not equivalent to editable native objects.

## D. Metadata discovery sources

### 13. Crossref REST API
Official documentation: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- Provides DOI-based bibliographic metadata and deposited license information.
- Design decision: use as one metadata source; preserve the provider record and do not infer image rights from paper availability.

### 14. OpenAlex API
Official documentation: https://help.openalex.org/api/
- Provides works, authors, sources, institutions, search, filters, grouping and selected fields.
- Design decision: use for paper discovery and metadata enrichment, with canonical DOI/arXiv/OpenReview IDs and source provenance retained.

### 15. OpenReview API
Official API guide: https://docs.openreview.net/getting-started/using-the-api
- API 2 is current; API 1 remains relevant for some older conferences.
- API access follows the account's permissions.
- Design decision: conference adapters must normalize API versions and preserve the original forum/note identifiers.

## E. External implementation being compared

### 16. Top-Conf Paper Figure Gallery
Repository: https://github.com/qwdwqfwq/topconf-paper-figure-gallery
- Relevant areas: methodology, figure extraction, filtering, retrieval, FigureForge and editable export documentation.
- Design decision: borrow the metadata-first gallery concept, visual reference retrieval and two-pass reference analysis; do not copy third-party paper-image binaries without checking per-asset rights.

## F. Interpretation boundaries

- A model's semantic similarity score is not a relevance judgment.
- A retrieved figure is not automatically a suitable design reference.
- A layout detector's class is not a scientific design taxonomy.
- An SVG that parses is not necessarily readable at final publication size.
- A draw.io or PPTX file is not meaningfully editable if it contains only one flattened bitmap.
- A successful test suite validates implemented contracts, not the scientific correctness of arbitrary future figures.
