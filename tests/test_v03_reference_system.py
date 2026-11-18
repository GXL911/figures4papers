import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from figures4papers.reference_atlas import (
    AtlasValidationError, FigureRecord, ReferenceAtlas, reciprocal_rank_fusion,
)
from figures4papers.retrieval_eval import (
    evaluate_queries, ndcg_at_k, recall_at_k, reciprocal_rank,
)
from figures4papers.design_contracts import (
    DesignContractError, render_scene_svg, validate_design_brief, validate_scene, validate_scene_against_brief,
)
from figures4papers.drawio_export import export_drawio, scene_to_drawio_xml

ROOT = Path(__file__).resolve().parents[1]
ATLAS_DIR = ROOT / "data" / "reference-atlas"


def load_atlas():
    return ReferenceAtlas.from_directory(ATLAS_DIR)


def sample_scene():
    return {
        "schema_version": "1.0",
        "figure_id": "scene-test",
        "title": "A small scientific mechanism",
        "description": "Input branches into two operators and is fused.",
        "canvas": {"width_mm": 120, "height_mm": 70, "units": "mm"},
        "layout": {"mode": "manual", "engine": "manual"},
        "nodes": [
            {"id": "input", "type": "box", "label": "Input", "x_mm": 4, "y_mm": 27,
             "width_mm": 22, "height_mm": 16, "style_token": "primary"},
            {"id": "left", "type": "box", "label": "Local", "x_mm": 42, "y_mm": 8,
             "width_mm": 25, "height_mm": 16, "style_token": "accent"},
            {"id": "right", "type": "box", "label": "Global", "x_mm": 42, "y_mm": 46,
             "width_mm": 25, "height_mm": 16, "style_token": "secondary"},
            {"id": "output", "type": "box", "label": "Output", "x_mm": 88, "y_mm": 27,
             "width_mm": 26, "height_mm": 16, "style_token": "primary"},
        ],
        "edges": [
            {"id": "input-local", "source": "input", "target": "left", "kind": "data_flow"},
            {"id": "input-global", "source": "input", "target": "right", "kind": "data_flow"},
            {"id": "local-output", "source": "left", "target": "output", "kind": "data_flow"},
            {"id": "global-output", "source": "right", "target": "output", "kind": "data_flow"},
        ],
    }


def test_seed_atlas_is_metadata_only_and_linked():
    atlas = load_atlas()
    assert len(atlas.papers) == 16
    assert len(atlas.figures) == 16
    assert all(fig.paper_id in atlas.papers for fig in atlas.figures.values())
    assert all(fig.rights_status == "reference_only" for fig in atlas.figures.values())
    assert all(fig.local_asset is None for fig in atlas.figures.values())


def test_fielded_bm25_finds_selective_ssm_reference():
    hits = load_atlas().search("selective state space input dependent hardware aware scan", limit=5)
    assert hits
    assert hits[0].figure.figure_id == "mamba-2023-fig1"
    assert hits[0].lexical_score > 0


def test_evidence_type_is_an_independent_retrieval_facet():
    hits = load_atlas().search(
        "nominal empirical coverage calibration uncertainty",
        filters={"evidence_types": ["calibration"]},
        facets={"evidence_types": ["reliability", "uncertainty"]},
        limit=5,
    )
    assert {hit.figure.figure_id for hit in hits} == {"guo-2017-fig1", "kuleshov-2018-fig1"}


def test_hard_filter_and_soft_structural_ranking():
    atlas = load_atlas()
    hits = atlas.search(
        "top k expert routing token dispatch",
        filters={"domains": "mixture_of_experts"},
        facets={"figure_role": "routing_architecture"},
        limit=5,
    )
    assert {hit.figure.figure_id for hit in hits} == {"moe-2017-fig1", "switch-2021-fig1"}
    assert hits[0].structural_score > 0


def test_semantic_scores_are_optional_and_fused_by_rank():
    atlas = load_atlas()
    hits = atlas.search(
        "attention architecture",
        semantic_scores={"gcn-2017-fig1": 0.99, "transformer-2017-fig1": 0.8},
        limit=5,
    )
    assert any(hit.figure.figure_id == "gcn-2017-fig1" for hit in hits)
    assert any(hit.semantic_score is not None for hit in hits)


def test_rrf_is_deterministic_and_rank_based():
    scores, ranks = reciprocal_rank_fusion({
        "lexical": ["a", "b", "c"],
        "semantic": ["b", "a"],
    }, k=60)
    assert scores["a"] == pytest.approx(1 / 61 + 1 / 62)
    assert scores["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert ranks["a"] == {"lexical": 1, "semantic": 2}


def test_retrieval_metrics_and_development_qrels():
    assert reciprocal_rank([0, 3], 5) == pytest.approx(0.5)
    assert recall_at_k([3, 0], total_relevant=2, k=2) == pytest.approx(0.5)
    assert 0 < ndcg_at_k([3, 0], [3, 2], 2) < 1
    queries = json.loads((ATLAS_DIR / "queries.json").read_text(encoding="utf-8"))
    report = evaluate_queries(load_atlas(), queries, k=5)
    assert report["query_count"] == 8
    assert set(report["macro_average"]) == {"mrr@5", "recall@5", "ndcg@5"}
    assert "not evidence of general retrieval quality" in report["interpretation"]


def test_scene_contract_and_svg_rendering():
    scene = sample_scene()
    assert validate_scene(scene)["figure_id"] == "scene-test"
    svg = render_scene_svg(scene)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert "Local" in svg and "Global" in svg
    assert "input-local" in svg


def test_drawio_export_contains_native_vertices_and_edges(tmp_path):
    scene = sample_scene()
    xml = scene_to_drawio_xml(scene)
    root = ET.fromstring(xml)
    assert root.tag == "mxfile"
    cells = root.findall(".//mxCell")
    assert sum(cell.attrib.get("vertex") == "1" for cell in cells) == 4
    assert sum(cell.attrib.get("edge") == "1" for cell in cells) == 4
    path = export_drawio(scene, tmp_path / "editable")
    assert path.suffix == ".drawio" and path.is_file()


def test_scene_rejects_dangling_edge_and_reserved_id():
    scene = sample_scene()
    scene["edges"][0]["target"] = "missing"
    with pytest.raises(DesignContractError):
        validate_scene(scene)
    scene = sample_scene()
    scene["nodes"][0]["id"] = "1"
    with pytest.raises(DesignContractError):
        validate_scene(scene)


def test_layered_layout_is_explicitly_not_faked():
    scene = sample_scene()
    scene["layout"] = {"mode": "layered", "engine": "elk-layered", "direction": "LR"}
    for node in scene["nodes"]:
        node.pop("x_mm")
        node.pop("y_mm")
    validate_scene(scene)
    with pytest.raises(NotImplementedError):
        render_scene_svg(scene)


def test_design_brief_requires_claim_to_content_mapping():
    brief = {
        "schema_version": "1.0",
        "brief_id": "brief-test",
        "research_question": "How does the operator route information?",
        "intended_takeaway": "Two pathways are fused before prediction.",
        "figure_role": "mechanism_explanation",
        "content_blocks": [
            {"id": "input", "label": "Input", "scientific_role": "source", "description": "Historical sequence"},
            {"id": "fusion", "label": "Fusion", "scientific_role": "operator", "description": "Combine local and global features"},
        ],
        "panel_plan": [
            {"panel_id": "a", "claim": "The input feeds two paths.", "visual_form": "block_diagram",
             "content_block_ids": ["input", "fusion"]}
        ],
        "references": [{"figure_id": "mamba-2023-fig1", "reason_for_use": "Mechanism plus systems context"}],
    }
    assert validate_design_brief(brief)["brief_id"] == "brief-test"
    brief["panel_plan"][0]["content_block_ids"] = ["not-a-real-block"]
    with pytest.raises(DesignContractError):
        validate_design_brief(brief)


def test_local_assets_require_explicit_rights():
    record = {
        "figure_id": "bad", "paper_id": "p", "figure_number": "Figure 1",
        "caption": "Caption", "summary": "Summary", "figure_role": "role",
        "visual_form": "block_diagram", "layout_patterns": ["left_to_right"],
        "scientific_intents": ["describe_architecture"], "domains": [], "methods": [],
        "tasks": [], "panel_count": 1, "rights_status": "reference_only",
        "curation_status": "provisional", "metadata_source_url": "https://example.org/paper",
        "local_asset": "images/figure.png",
    }
    with pytest.raises(AtlasValidationError):
        FigureRecord.from_dict(record)


def test_json_schemas_are_valid_json_documents():
    json.loads((ROOT / "schemas" / "design-brief.schema.json").read_text(encoding="utf-8"))
    json.loads((ROOT / "schemas" / "scene.schema.json").read_text(encoding="utf-8"))


def test_about_conv_design_brief_and_scene_are_semantically_linked():
    brief = json.loads((ROOT / "examples" / "hybrid_memory_design_brief.json").read_text(encoding="utf-8"))
    scene = json.loads((ROOT / "examples" / "hybrid_memory_scene.json").read_text(encoding="utf-8"))
    assert validate_scene_against_brief(brief, scene)["brief_id"] == brief["brief_id"]
    scene["nodes"][1]["content_block_id"] = "not-in-the-brief"
    with pytest.raises(DesignContractError):
        validate_scene_against_brief(brief, scene)
    scene = json.loads((ROOT / "examples" / "hybrid_memory_scene.json").read_text(encoding="utf-8"))
    scene["edges"] = scene["edges"][:-1]
    with pytest.raises(DesignContractError):
        validate_scene_against_brief(brief, scene)
