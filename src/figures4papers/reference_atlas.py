"""Metadata-first scientific figure reference atlas and hybrid retrieval.

The v0.3 baseline deliberately stores bibliographic metadata and curated figure
descriptions, not third-party figure binaries. Optional semantic scores can be
supplied by an embedding adapter without making CLIP a core dependency.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sysconfig
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

_TOKEN_RE = re.compile(r"[^\W_]+", flags=re.UNICODE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "into", "is", "of", "on", "or", "the", "to", "using", "with", "via",
}
FIELD_WEIGHTS = {
    "title": 3.0,
    "caption": 2.4,
    "keywords": 2.2,
    "summary": 1.8,
    "abstract": 1.3,
    "figure_role": 1.2,
    "visual_form": 1.1,
    "layout": 0.9,
    "venue": 0.3,
}
RIGHTS_STATUSES = {"reference_only", "open_license", "permission_confirmed", "unknown"}


class AtlasValidationError(ValueError):
    """Invalid or internally inconsistent reference-atlas data."""


def tokenize(text: str) -> list[str]:
    """Small deterministic tokenizer; no stemming or hidden model dependency."""
    return [
        token for token in _TOKEN_RE.findall(str(text).casefold())
        if token not in _STOPWORDS
    ]


def _required_text(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AtlasValidationError(f"{key} must be a nonblank string.")
    return value.strip()


def _text_list(data: Mapping[str, Any], key: str, *, required: bool = False) -> tuple[str, ...]:
    value = data.get(key, [])
    if value is None:
        value = []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise AtlasValidationError(f"{key} must be a list of nonblank strings.")
    result = tuple(item.strip() for item in value)
    if required and not result:
        raise AtlasValidationError(f"{key} must contain at least one item.")
    return result


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    authors: tuple[str, ...]
    year: int
    venue: str
    paper_url: str
    abstract: str = ""
    doi: str | None = None
    arxiv_id: str | None = None
    metadata_source_url: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PaperRecord":
        year = data.get("year")
        if not isinstance(year, int) or year < 1900 or year > 2200:
            raise AtlasValidationError("paper.year must be a plausible integer.")
        return cls(
            paper_id=_required_text(data, "paper_id"),
            title=_required_text(data, "title"),
            authors=_text_list(data, "authors", required=True),
            year=year,
            venue=_required_text(data, "venue"),
            paper_url=_required_text(data, "paper_url"),
            abstract=str(data.get("abstract", "")).strip(),
            doi=data.get("doi"),
            arxiv_id=data.get("arxiv_id"),
            metadata_source_url=data.get("metadata_source_url"),
        )


@dataclass(frozen=True)
class FigureRecord:
    figure_id: str
    paper_id: str
    figure_number: str
    caption: str
    summary: str
    figure_role: str
    visual_form: str
    layout_patterns: tuple[str, ...]
    scientific_intents: tuple[str, ...]
    evidence_types: tuple[str, ...]
    domains: tuple[str, ...>
    methods: tuple[str, ...]
    tasks: tuple[str, ...]
    panel_count: int
    page: int | None
    rights_status: str
    curation_status: str
    metadata_source_url: str
    figure_url: str | None = None
    local_asset: str | None = None
    license: str | None = None
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FigureRecord":
        panel_count = data.get("panel_count", 1)
        page = data.get("page")
        if not isinstance(panel_count, int) or panel_count < 1:
            raise AtlasValidationError("figure.panel_count must be a positive integer.")
        if page is not None and (not isinstance(page, int) or page < 1):
            raise AtlasValidationError("figure.page must be a positive 1-based page number.")
        rights_status = _required_text(data, "rights_status")
        if rights_status not in RIGHTS_STATUSES:
            raise AtlasValidationError(f"Unsupported rights_status: {rights_status}")
        local_asset = data.get("local_asset")
        license_name = data.get("license")
        if local_asset and (rights_status not in {"open_license", "permission_confirmed"} or not license_name):
            raise AtlasValidationError(
                "A local figure asset requires an open-license or permission-confirmed status and a license."
            )
        curation_status = _required_text(data, "curation_status")
        if curation_status not in {"curated", "machine_extracted", "provisional"}:
            raise AtlasValidationError(f"Unsupported curation_status: {curation_status}")
        return cls(
            figure_id=_required_text(data, "figure_id"),
            paper_id=_required_text(data, "paper_id"),
            figure_number=_required_text(data, "figure_number"),
            caption=_required_text(data, "caption"),
            summary=_required_text(data, "summary"),
            figure_role=_required_text(data, "figure_role"),
            visual_form=_required_text(data, "visual_form"),
            layout_patterns=_text_list(data, "layout_patterns", required=True),
            scientific_intents=_text_list(data, "scientific_intents", required=True),
            evidence_types=_text_list(data, "evidence_types"),
            domains=_text_list(data, "domains"),
            methods=_text_list(data, "methods"),
            tasks=_text_list(data, "tasks"),
            panel_count=panel_count,
            page=page,
            rights_status=rights_status,
            curation_status=curation_status,
            metadata_source_url=_required_text(data, "metadata_source_url"),
            figure_url=data.get("figure_url"),
            local_asset=local_asset,
            license=license_name,
            notes=str(data.get("notes", "")).strip(),
        )


@dataclass(frozen=True)
class SearchHit:
    figure: FigureRecord
    paper: PaperRecord
    lexical_score: float
    structural_score: float
    semantic_score: float | None
    rrf_score: float
    source_ranks: Mapping[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "figure_id": self.figure.figure_id,
            "paper_id": self.paper.paper_id,
            "paper_title": self.paper.title,
            "year": self.paper.year,
            "venue": self.paper.venue,
            "paper_url": self.paper.paper_url,
            "figure_number": self.figure.figure_number,
            "caption": self.figure.caption,
            "summary": self.figure.summary,
            "figure_role": self.figure.figure_role,
            "visual_form": self.figure.visual_form,
            "layout_patterns": list(self.figure.layout_patterns),
            "scientific_intents": list(self.figure.scientific_intents),
            "domains": list(self.figure.domains),
            "methods": list(self.figure.methods),
            "tasks": list(self.figure.tasks),
            "rights_status": self.figure.rights_status,
            "curation_status": self.figure.curation_status,
            "scores": {
                "bm25": self.lexical_score,
                "structural": self.structural_score,
                "semantic": self.semantic_score,
                "rrf": self.rrf_score,
            },
            "source_ranks": dict(self.source_ranks),
        }


class _FieldedBM25:
    """Fielded BM25 with per-field length normalization and explicit boosts."""

    def __init__(
        self,
        documents: Sequence[tuple[str, Mapping[str, str]]],
        *,
        field_weights: Mapping[str, float] = FIELD_WEIGHTS,
        k1: float = 1.2,
        b: float = 0.75,
    ):
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 requires k1 > 0 and b in [0, 1].")
        self.documents = list(documents)
        self.field_weights = dict(field_weights)
        self.k1, self.b = float(k1), float(b)
        self.term_frequencies: dict[str, list[Counter[str]]] = {}
        self.lengths: dict[str, list[int]] = {}
        self.document_frequencies: dict[str, Counter[str]] = {}
        self.average_lengths: dict[str, float] = {}
        count = len(self.documents)
        for field in self.field_weights:
            counters = [Counter(tokenize(fields.get(field, ""))) for _, fields in self.documents]
            lengths = [sum(counter.values()) for counter in counters]
            document_frequency: Counter[str] = Counter()
            for counter in counters:
                document_frequency.update(counter.keys())
            self.term_frequencies[field] = counters
            self.lengths[field] = lengths
            self.document_frequencies[field] = document_frequency
            self.average_lengths[field] = (sum(lengths) / count) if count else 0.0

    def score(self, query: str) -> dict[str, float]:
        terms = set(tokenize(query))
        scores = {doc_id: 0.0 for doc_id, _ in self.documents}
        n_docs = len(self.documents)
        if not terms or not n_docs:
            return scores
        for field, weight in self.field_weights.items():
            avgdl = self.average_lengths[field]
            if avgdl <= 0:
                continue
            frequencies = self.term_frequencies[field]
            lengths = self.lengths[field]
            dfs = self.document_frequencies[field]
            for term in terms:
                df = dfs.get(term, 0)
                if df == 0:
                    continue
                idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                for index, counter in enumerate(frequencies):
                    tf = counter.get(term, 0)
                    if tf == 0:
                        continue
                    dl = lengths[index]
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * dl / avgdl)
                    scores[self.documents[index][0]] += weight * idf * (tf * (self.k1 + 1.0)) / denominator
        return scores


def reciprocal_rank_fusion(
    rankings: Mapping[str, Sequence[str]],
    *,
    k: int = 60,
    weights: Mapping[str, float] | None = None,
) -> tuple[dict[str, float], dict[str, dict[str, int]]]:
    """Fuse ranked ID lists without mixing incomparable raw score scales."""
    if k < 0:
        raise ValueError("RRF k must be nonnegative.")
    weights = dict(weights or {})
    fused: dict[str, float] = {}
    ranks: dict[str, dict[str, int]] = {}
    for source, ranking in rankings.items():
        weight = float(weights.get(source, 1.0))
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("RRF source weights must be finite and nonnegative.")
        seen: set[str] = set()
        for rank, item_id in enumerate(ranking, start=1):
            if item_id in seen:
                continue
            seen.add(item_id)
            fused[item_id] = fused.get(item_id, 0.0) + weight / (k + rank)
            ranks.setdefault(item_id, {})[source] = rank
    return fused, ranks


class ReferenceAtlas:
    """Validated in-memory atlas with lexical, facet and optional semantic retrieval."""

    def __init__(self, papers: Sequence[PaperRecord], figures: Sequence[FigureRecord]):
        self.papers = {paper.paper_id: paper for paper in papers}
        self.figures = {figure.figure_id: figure for figure in figures}
        if len(self.papers) != len(papers):
            raise AtlasValidationError("paper_id values must be unique.")
        if len(self.figures) != len(figures):
            raise AtlasValidationError("figure_id values must be unique.")
        missing = sorted({figure.paper_id for figure in figures} - set(self.papers))
        if missing:
            raise AtlasValidationError(f"Figures refer to unknown paper_id values: {missing}")

    @classmethod
    def from_directory(cls, directory: str | Path) -> "ReferenceAtlas":
        root = Path(directory)
        def read_jsonl(name: str) -> list[dict[str, Any]]:
            path = root / name
            if not path.is_file():
                raise FileNotFoundError(str(path))
            rows = []
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise AtlasValidationError(f"{path}:{line_number}: {exc}") from exc
            return rows
        papers = [PaperRecord.from_dict(row) for row in read_jsonl("papers.jsonl")]
        figures = [FigureRecord.from_dict(row) for row in read_jsonl("figures.jsonl")]
        return cls(papers, figures)

    def _fields(self, figure: FigureRecord, paper: PaperRecord) -> dict[str, str]:
        return {
            "title": paper.title,
            "abstract": paper.abstract,
            "caption": figure.caption,
            "summary": figure.summary,
            "keywords": " ".join(
                figure.scientific_intents + figure.evidence_types + figure.domains + figure.methods + figure.tasks
            ),
            "figure_role": figure.figure_role,
            "visual_form": figure.visual_form,
            "layout": " ".join(figure.layout_patterns),
            "venue": paper.venue,
        }

    @staticmethod
    def _values(value: Any) -> set[str]:
        if value is None:
            return set()
        if isinstance(value, str):
            return {value.casefold()}
        if isinstance(value, (list, tuple, set)):
            return {str(item).casefold() for item in value}
        raise ValueError("Facet values must be strings or lists of strings.")

    def _passes_filters(self, figure: FigureRecord, paper: PaperRecord, filters: Mapping[str, Any]) -> bool:
        field_map = {
            "figure_role": {figure.figure_role.casefold()},
            "visual_form": {figure.visual_form.casefold()},
            "layout_patterns": {item.casefold() for item in figure.layout_patterns},
            "scientific_intents": {item.casefold() for item in figure.scientific_intents},
            "evidence_types": {item.casefold() for item in figure.evidence_types},
            "domains": {item.casefold() for item in figure.domains},
            "methods": {item.casefold() for item in figure.methods},
            "tasks": {item.casefold() for item in figure.tasks},
            "venue": {paper.venue.casefold()},
        }
        for key, value in filters.items():
            if key == "year_min" and paper.year < int(value):
                return False
            if key == "year_max" and paper.year > int(value):
                return False
            if key not in field_map:
                raise ValueError(f"Unknown reference-atlas filter: {key}")
            expected = self._values(value)
            if expected and not (field_map[key] & expected):
                return False
        return True

    def _structural_score(self, figure: FigureRecord, facets: Mapping[str, Any]) -> float:
        field_map = {
            "figure_role": {figure.figure_role.casefold()},
            "visual_form": {figure.visual_form.casefold()},
            "layout_patterns": {item.casefold() for item in figure.layout_patterns},
            "scientific_intents": {item.casefold() for item in figure.scientific_intents},
            "evidence_types": {item.casefold() for item in figure.evidence_types},
            "domains": {item.casefold() for item in figure.domains},
            "methods": {item.casefold() for item in figure.methods},
            "tasks": {item.casefold() for item in figure.tasks},
        }
        weights = {
            "figure_role": 3.0, "visual_form": 2.5, "layout_patterns": 2.0,
            "scientific_intents": 1.8, "evidence_types": 0.9, "domains": 1.2, "methods": 1.2, "tasks": 1.0,
        }
        score = 0.0
        for key, value in facets.items():
            if key not in field_map:
                raise ValueError(f"Unknown reference-atlas facet: {key}")
            score += weights[key] * len(field_map[key] & self._values(value))
        return score

    def search(
        self,
        query: str = "",
        *,
        limit: int = 10,
        filters: Mapping[str, Any] | None = None,
        facets: Mapping[str, Any] | None = None,
        semantic_scores: Mapping[str, float] | None = None,
        rrf_k: int = 60,
        rrf_weights: Mapping[str, float] | None = None,
    ) -> list[SearchHit]:
        """Search references; semantic_scores is an optional embedding-adapter hook.

        Hard filters constrain eligibility. Soft facets contribute a separate
        structural ranking. Optional semantic scores must be keyed by figure_id.
        """
        if limit < 1:
            raise ValueError("limit must be positive.")
        filters, facets = dict(filters or {}), dict(facets or {})
        semantic_scores = dict(semantic_scores or {})
        if not query.strip() and not facets and not semantic_scores:
            raise ValueError("Provide a text query, soft facets, or semantic scores.")
        eligible = [
            figure for figure in self.figures.values()
            if self._passes_filters(figure, self.papers[figure.paper_id], filters)
        ]
        if not eligible:
            return []
        documents = [
            (figure.figure_id, self._fields(figure, self.papers[figure.paper_id]))
            for figure in eligible
        ]
        lexical_scores = _FieldedBM25(documents).score(query) if query.strip() else {
            figure.figure_id: 0.0 for figure in eligible
        }
        lexical_ranking = [
            item_id for item_id, score in sorted(
                lexical_scores.items(), key=lambda item: (-item[1], item[0])
            ) if score > 0
        ]
        structural_scores = {
            figure.figure_id: self._structural_score(figure, facets) for figure in eligible
        }
        structural_ranking = [
            item_id for item_id, score in sorted(
                structural_scores.items(), key=lambda item: (-item[1], item[0])
            ) if score > 0
        ]
        valid_ids = {figure.figure_id for figure in eligible}
        clean_semantic = {}
        for item_id, score in semantic_scores.items():
            value = float(score)
            if item_id in valid_ids and math.isfinite(value):
                clean_semantic[item_id] = value
        semantic_ranking = [
            item_id for item_id, _ in sorted(
                clean_semantic.items(), key=lambda item: (-item[1], item[0])
            )
        ]
        rankings: dict[str, Sequence[str]] = {}
        if lexical_ranking:
            rankings["lexical"] = lexical_ranking
        if structural_ranking:
            rankings["structural"] = structural_ranking
        if semantic_ranking:
            rankings["semantic"] = semantic_ranking
        fused, source_ranks = reciprocal_rank_fusion(
            rankings, k=rrf_k, weights=rrf_weights
        )
        ordered_ids = sorted(fused, key=lambda item_id: (-fused[item_id], item_id))[:limit]
        return [
            SearchHit(
                figure=self.figures[item_id],
                paper=self.papers[self.figures[item_id].paper_id],
                lexical_score=lexical_scores.get(item_id, 0.0),
                structural_score=structural_scores.get(item_id, 0.0),
                semantic_score=clean_semantic.get(item_id),
                rrf_score=fused[item_id],
                source_ranks=source_ranks.get(item_id, {}),
            )
            for item_id in ordered_ids
        ]


def _default_atlas_dir() -> Path:
    source_checkout = Path(__file__).resolve().parents[2] / "data" / "reference-atlas"
    if source_checkout.is_dir():
        return source_checkout
    installed_data = Path(sysconfig.get_path("data")) / "share" / "figures4papers" / "reference-atlas"
    if installed_data.is_dir():
        return installed_data
    return source_checkout


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search the figures4papers reference atlas.")
    parser.add_argument("--atlas", type=Path, default=_default_atlas_dir())
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--figure-role")
    parser.add_argument("--visual-form")
    parser.add_argument("--domain")
    args = parser.parse_args(argv)
    atlas = ReferenceAtlas.from_directory(args.atlas)
    filters = {}
    if args.figure_role:
        filters["figure_role"] = args.figure_role
    if args.visual_form:
        filters["visual_form"] = args.visual_form
    if args.domain:
        filters["domains"] = args.domain
    hits = atlas.search(args.query, limit=args.limit, filters=filters)
    print(json.dumps([hit.to_dict() for hit in hits], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
