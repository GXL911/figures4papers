import json
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
from jsonschema import Draft202012Validator

from figures4papers import (
    FigureContract,
    ReferenceAtlas,
    audit_scene_geometry,
    audit_svg,
    build_manifest,
    scene_to_drawio_xml,
    validate_design_brief,
    validate_renderer_capabilities,
    validate_scene,
    validate_scene_against_brief,
)
from figures4papers.design_contracts import DesignContractError
from figures4papers.reference_atlas import AtlasValidationError
from figures4papers.retrieval_eval import main as evaluate_reference_atlas

ROOT = Path(__file__).resolve().parents[1]
ATLAS_DIR = ROOT / "data" / "reference-atlas"


def load_atlas():
    return ReferenceAtlas.from_directory(ATLAS_DIR)


def load_examples():
    brief = json.loads((ROOT / "examples" / "hybrid_memory_design_brief.json").read_text(encoding="utf-8"))
    scene = json.loads((ROOT / "examples" / "hybrid_memory_scene.json").read_text(encoding="utf-8"))
    return brief, scene


def test_atlas_loads_and_enforces_all_controlled_vocabulary():
    atlas = load_atlas()
    assert atlas.taxonomy["taxonomy_version"] == "1.0"
    assert len(atlas.papers) == 16
    assert len(atlas.figures) == 16
    assert all(fig.figure_role in atlas.taxonomy["figure_roles"] for fig in atlas.figures.values())
    assert all(fig.visual_form in atlas.taxonomy["visual_forms"] for fig in atlas.figures.values())


def test_atlas_rejects_undefined_controlled_vocabulary(tmp_path):
    copied = tmp_path / "atlas"
    shutil.copytree(ATLAS_DIR, copied)
    rows = [json.loads(line) for line in (copied / "figures.jsonl").read_text().splitlines() if line.strip()]
    rows[0]["figure_role"] = "made_up_role"
    (copied / "figures.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    with pytest.raises(AtlasValidationError, match="outside taxonomy"):
        ReferenceAtlas.from_directory(copied)


def test_year_filters_are_inclusive_and_validate_arguments():
    atlas = load_atlas()
    figure = next(iter(atlas.figures.values()))
    paper = atlas.papers[figure.paper_id]
    assert atlas._passes_filters(figure, paper, {"year_min": paper.year})
    assert atlas._passes_filters(figure, paper, {"year_max": paper.year})
    assert not atlas._passes_filters(figure, paper, {"year_min": paper.year + 1})
    assert not atlas._passes_filters(figure, paper, {"year_max": paper.year - 1})
    with pytest.raises(ValueError, match="year_min must be an integer"):
        atlas._passes_filters(figure, paper, {"year_min": True})
    with pytest.raises(ValueError, match="must not exceed"):
        atlas._passes_filters(figure, paper, {"year_min": 2024, "year_max": 2020})


def test_search_hit_exposes_reference_locator_and_provenance():
    hit = load_atlas().search("selective state space hardware-aware scan", limit=1)[0]
    result = hit.to_dict()
    assert result["figure_locator"]["figure_number"] == hit.figure.figure_number
    assert "page" in result["figure_locator"]
    assert result["metadata_source_url"] == hit.figure.metadata_source_url
    assert result["paper_url"] == hit.paper.paper_url


def test_design_brief_requires_every_block_to_be_assigned_to_a_panel():
    brief, _ = load_examples()
    brief["panel_plan"][0]["content_block_ids"].remove("global_ssm")
    with pytest.raises(DesignContractError, match="not assigned to any panel"):
        validate_design_brief(brief)


def test_brief_scene_requires_id_role_and_satisfies_constraints():
    brief, scene = load_examples()
    assert validate_scene_against_brief(brief, scene, atlas=load_atlas())["brief_id"] == brief["brief_id"]
    missing_id = dict(scene)
    missing_id.pop("brief_id")
    with pytest.raises(DesignContractError, match="brief_id"):
        validate_scene_against_brief(brief, missing_id)
    bad_role = json.loads(json.dumps(scene))
    bad_role["nodes"][1].pop("scientific_role")
    with pytest.raises(DesignContractError, match="must declare scientific_role"):
        validate_scene_against_brief(brief, bad_role)


def test_brief_scene_rejects_dimension_and_font_constraint_violations():
    brief, scene = load_examples()
    wrong_size = json.loads(json.dumps(scene))
    wrong_size["canvas"]["width_mm"] = 177
    with pytest.raises(DesignContractError, match="target_width_mm"):
        validate_scene_against_brief(brief, wrong_size)
    small_font = json.loads(json.dumps(scene))
    small_font["nodes"][1]["font_size_pt"] = 7
    with pytest.raises(DesignContractError, match="below minimum_font_size_pt"):
        validate_scene_against_brief(brief, small_font)


def test_typed_graph_path_does_not_mix_relation_kinds():
    brief = {
        "schema_version": "1.0",
        "brief_id": "typed-path",
        "research_question": "Does a typed path exist?",
        "intended_takeaway": "Only same-kind edges satisfy a typed path.",
        "figure_role": "mechanism_explanation",
        "content_blocks": [
            {"id": "a", "label": "A", "scientific_role": "source", "description": "Source"},
            {"id": "b", "label": "B", "scientific_role": "operator", "description": "Intermediate"},
            {"id": "c", "label": "C", "scientific_role": "prediction", "description": "Target"},
        ],
        "panel_plan": [{
            "panel_id": "p", "claim": "A path is required.", "visual_form": "block_diagram",
            "content_block_ids": ["a", "b", "c"],
        }],
        "required_relations": [{
            "source_block_id": "a", "target_block_id": "c",
            "relation_type": "data_flow", "must_be_direct": False,
        }],
    }
    scene = {
        "schema_version": "1.0", "figure_id": "typed-path-scene", "title": "Typed path",
        "brief_id": "typed-path",
        "canvas": {"width_mm": 100, "height_mm": 40, "units": "mm"},
        "layout": {"mode": "manual", "engine": "manual", "direction": "LR"},
        "nodes": [
            {"id": "a", "type": "box", "label": "A", "x_mm": 2, "y_mm": 10,
             "width_mm": 15, "height_mm": 15, "content_block_id": "a",
             "scientific_role": "source", "panel_id": "p"},
            {"id": "b", "type": "box", "label": "B", "x_mm": 40, "y_mm": 10,
             "width_mm": 15, "height_mm": 15, "content_block_id": "b",
             "scientific_role": "operator", "panel_id": "p"},
            {"id": "c", "type": "box", "label": "C", "x_mm": 78, "y_mm": 10,
             "width_mm": 15, "height_mm": 15, "content_block_id": "c",
             "scientific_role": "prediction", "panel_id": "p"},
        ],
        "edges": [
            {"id": "ab", "source": "a", "target": "b", "kind": "control_flow"},
            {"id": "bc", "source": "b", "target": "c", "kind": "data_flow"},
        ],
    }
    with pytest.raises(DesignContractError, match="typed relation"):
        validate_scene_against_brief(brief, scene)


def test_renderer_capability_rejects_unimplemented_self_loop():
    scene = {
        "schema_version": "1.0", "figure_id": "loop", "title": "Loop",
        "canvas": {"width_mm": 40, "height_mm": 40, "units": "mm"},
        "layout": {"mode": "manual", "engine": "manual"},
        "nodes": [{"id": "a", "type": "box", "label": "A", "x_mm": 5, "y_mm": 5,
                   "width_mm": 20, "height_mm": 20}],
        "edges": [{"id": "loop-edge", "source": "a", "target": "a", "kind": "self_loop"}],
    }
    validate_scene(scene)
    with pytest.raises(NotImplementedError, match="self-loop"):
        validate_renderer_capabilities(scene, "svg")
    with pytest.raises(NotImplementedError, match="self-loop"):
        validate_renderer_capabilities(scene, "drawio")


def test_orthogonal_route_is_supported_by_both_renderers():
    _, scene = load_examples()
    scene["edges"][0]["route"] = "orthogonal"
    from figures4papers import render_scene_svg
    svg = render_scene_svg(scene)
    assert "input-to-local" in svg
    xml = ET.fromstring(scene_to_drawio_xml(scene))
    assert any("orthogonalEdgeStyle" in obj.find("mxCell").attrib["style"] for obj in xml.findall(".//object"))


def test_drawio_preserves_subtitle_semantics_and_converts_pt_to_px():
    _, scene = load_examples()
    xml = scene_to_drawio_xml(scene)
    root = ET.fromstring(xml)
    input_obj = next(obj for obj in root.findall(".//object") if obj.attrib["id"] == "input")
    assert "sequence x[t]" in input_obj.attrib["label"]
    assert input_obj.attrib["content_block_id"] == "input"
    assert input_obj.attrib["scientific_role"] == "source"
    style = input_obj.find("mxCell").attrib["style"]
    assert "fontSize=10.67" in style


def test_visual_qa_converts_css_pixels_to_points():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" role="img">'
        "<title>Test</title><text font-size=\"8px\">A</text></svg>"
    )
    report = audit_svg(svg, min_font_pt=7)
    assert report["minimum_declared_font_pt"] == pytest.approx(6)
    assert "small_text" in report["issues"]


def test_geometry_qa_detects_node_overlap():
    _, scene = load_examples()
    scene["nodes"][1]["x_mm"] = 10
    report = audit_scene_geometry(scene)
    assert report["overlapping_node_pairs"]
    assert "node_overlap" in report["issues"]


def test_json_schemas_are_formally_valid_and_accept_examples():
    brief, scene = load_examples()
    for schema_name, example in (
        ("design-brief.schema.json", brief),
        ("scene.schema.json", scene),
    ):
        schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(example)


def test_manifest_hashes_all_sources_and_outputs_and_records_metadata(tmp_path):
    source = tmp_path / "source.json"
    output = tmp_path / "figure.svg"
    source.write_text('{"source": true}', encoding="utf-8")
    output.write_text("<svg></svg>", encoding="utf-8")
    contract = FigureContract(
        figure_id="manifest-test", chart_type="other", takeaway="A tested takeaway",
        source_description="Test source", x_unit="mm", y_unit="mm",
    )
    manifest = build_manifest(
        contract=contract, source_files=(source,), output_files=(output,),
        transformations=("test transform",), metadata={"brief_id": "brief-1"},
    )
    assert len(manifest["sources"][0]["sha256"]) == 64
    assert len(manifest["outputs"][0]["sha256"]) == 64
    assert manifest["metadata"]["brief_id"] == "brief-1"
    assert manifest["versions"]["figures4papers"] != "0.2.0"


def test_reference_eval_uses_queries_from_selected_atlas_directory(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert evaluate_reference_atlas(["--atlas", str(ATLAS_DIR), "--k", "5"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["query_count"] == 8


def test_brief_reference_ids_are_checked_against_the_atlas():
    brief, scene = load_examples()
    brief["references"][0]["figure_id"] = "not-in-the-reference-atlas"
    with pytest.raises(DesignContractError, match="unknown Atlas figure IDs"):
        validate_scene_against_brief(brief, scene, atlas=load_atlas())


def test_schema_rejects_unknown_brief_properties():
    brief, _ = load_examples()
    brief["unreviewed_field"] = "must not silently pass"
    with pytest.raises(DesignContractError, match="Additional properties"):
        validate_design_brief(brief)


def test_renderer_rejects_spline_routing_before_export():
    _, scene = load_examples()
    scene["edges"][0]["route"] = "spline"
    with pytest.raises(NotImplementedError, match="spline"):
        validate_renderer_capabilities(scene, "svg")


def test_brief_minimum_font_applies_to_edge_labels():
    brief, scene = load_examples()
    scene["edges"][0]["label"] = "historical input"
    scene["edges"][0]["font_size_pt"] = 6.5
    with pytest.raises(DesignContractError, match="Edge .* below minimum_font_size_pt"):
        validate_scene_against_brief(brief, scene)
