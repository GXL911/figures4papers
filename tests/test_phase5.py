import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import pytest

from figures4papers import FigureContract
from figures4papers.layout_review import review_layout

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "examples")]
from image_signature import signature, signature_delta
from reproduce_legacy import CASES, output_key, check_baseline
from _render_legacy import TEX_SCRIPTS, portable_source
from immunostruct_publication import PANELS, panel_data, render_all


def test_script_manifest_and_output_identity():
    scripts = {p.relative_to(ROOT).as_posix() for p in ROOT.glob("figure_*/*.py") if p.name != "raw_data.py" and p.parent.name != "figure_benchmark"}
    assert scripts == {case.script for case in CASES}
    assert len(CASES) == len(scripts) == 29
    keys = [output_key(case, name) for case in CASES for name in case.outputs]
    assert len(keys) == len(set(keys)) == 45
    throughput = [key for key in keys if key.endswith("/results_comparison_speed.png")]
    assert len(throughput) == 2 and throughput[0] != throughput[1]


@pytest.mark.parametrize("path", sorted(TEX_SCRIPTS))
def test_portable_rewrite_scoped(path):
    source = (ROOT / path).read_text(encoding="utf-8")
    rewritten, operations = portable_source(path, source)
    compile(rewritten, path, "exec")
    assert "['text.usetex'] = False" in rewritten and operations
    assert len(source.splitlines()) == len(rewritten.splitlines())


def test_layout_checks_actual_text_and_placement():
    fig, ax = plt.subplots(figsize=(6, 3))
    try:
        ax.set_xlim(.35, .65)
        ax.locator_params(axis="x", nbins=3)
        fig.text(.45, .75, "first text", fontsize=11)
        fig.text(.45, .75, "second text", fontsize=11)
        fig.text(1.01, .3, "outside", fontsize=9)
        fig.text(.50, .92, "too small", fontsize=5)
        full = review_layout(fig, width_mm=152.4)
        assert ["first text", "second text"] in full["text_overlap_candidates"]
        assert full["outside_canvas"] == ["outside"]
        assert full["small_text"] == [{"text": "too small", "pt": 5}]
        assert len(review_layout(fig, width_mm=76.2)["small_text"]) > len(full["small_text"])
    finally:
        plt.close(fig)


def test_regression_rejects_large_change_and_missing_keys():
    old = signature(Image.new("RGB", (96, 64), "white"))
    assert signature_delta(old, old) == {"mae": 0, "changed_tiles": 0, "aspect": 0}
    new = signature(Image.new("RGB", (96, 64), "black"))
    case = CASES[0]
    key = output_key(case, case.outputs[0])
    row = {"script": case.script, "outputs": {case.outputs[0]: {"signature": new, "layout": None}}}
    errors = check_baseline([row], {
        key: {"signature": old, "layout_counts": None},
        "missing.png": {"signature": old, "layout_counts": None},
    })
    assert any("portable render changed" in e for e in errors)
    assert any("missing.png" in e for e in errors)


def test_mixed_uncertainty_validation():
    args = ("example", "other", "Comparison", "paper", "score", "method")
    with pytest.raises(ValueError, match="two explicit"):
        FigureContract(*args, uncertainty_kind="mixed", uncertainty_by_metric={"AUROC": "sd"})
    with pytest.raises(ValueError, match="requires"):
        FigureContract(*args, uncertainty_kind="sd", uncertainty_by_metric={"AUROC": "sd"})
    kinds = {"AUROC": "sd", "Mean PPVn": "sem"}
    contract = FigureContract(*args, uncertainty_kind="mixed", uncertainty_by_metric=kinds)
    kinds["AUROC"] = "sem"
    assert contract.to_dict()["uncertainty_by_metric"]["AUROC"] == "sd"


def test_immunostruct_preserves_reported_uncertainty_and_width(tmp_path):
    _, _, _, _, indices, _, means, err = panel_data("cedar_ablation")
    assert indices == [6, 4, 0]
    np.testing.assert_allclose(means[0], [.771, .433, .365])
    np.testing.assert_allclose(err[0], [.024, .069, .127 / np.sqrt(5)])
    results = render_all(tmp_path)
    assert set(results) == set(PANELS)
    for name, item in results.items():
        assert item["layout"]["small_text"] == item["layout"]["outside_canvas"] == item["layout"]["text_overlap_candidates"] == []
        assert len(item["outputs"]) == 3
        manifest = json.loads((tmp_path / f"{name}.manifest.json").read_text())
        assert manifest["figure_contract"]["uncertainty_by_metric"] == {"AUROC": "sd", "AUPRC": "sd", "Mean PPVn": "sem"}
        with Image.open(tmp_path / f"{name}.png") as im:
            assert abs(im.width / 300 * 25.4 - 178) < .15


def test_macl_cohort_shrinks_no_zero_padding(tmp_path):
    from macl_publication import retention_cohorts, render
    matrix = [[20, 0, 0], [18, 40, 0], [16, 43, 60]]
    cohorts = retention_cohorts(matrix)
    assert [len(x) for x in cohorts] == [3, 2, 1]
    np.testing.assert_allclose([x.mean() for x in cohorts], [0, .5, -4])
    render(tmp_path)
    output = json.loads((tmp_path / "retention-cohorts.json").read_text())
    assert output["qa"]["MACL-prev"]["task_count"] == [6, 5, 4, 3, 2, 1]


def test_rna_aggregate_axes_and_ranges(tmp_path):
    from rnagenscape_publication import load_table, render
    labels, pct = load_table("pct")
    _, delta = load_table("delta")
    assert pct.shape == delta.shape == (13, 6)
    assert labels[-1] == "RNAGenScape"
    np.testing.assert_allclose(pct[-1], [77.5, 97.9, 75, 85.1, 81.4, 67.8])
    assert delta[-1, 0] == .54 and delta[-1, 1] == -2.81
    render(tmp_path)
    assert {p.stem for p in tmp_path.glob("*.png")} == {"success_rate", "median_change"}
