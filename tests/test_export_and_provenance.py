import json
import matplotlib.pyplot as plt
import pytest
from figures4papers import FigureContract, finalize_figure, file_sha256, build_manifest

def contract():
    return FigureContract("fig-test","grouped_bar","Synthetic result",
                          "Test fixture","category","fraction")

def test_export_formats_manifest(tmp_path):
    source=tmp_path/"source.txt"
    source.write_text("immutable source",encoding="utf-8")
    fig,ax=plt.subplots()
    ax.plot([0,1],[0,1])
    paths=finalize_figure(fig,tmp_path/"chart",formats=["png","pdf","svg"],
                          contract=contract(),source_files=[source],
                          seed=5,transformations=["identity"])
    assert {p.suffix for p in paths}=={".png",".pdf",".svg"}
    data=json.loads((tmp_path/"chart.manifest.json").read_text(encoding="utf-8"))
    assert data["sources"][0]["sha256"]==file_sha256(source)
    assert data["outputs"][0]["sha256"]==file_sha256(paths[0])
    assert data["figure_contract"]["figure_id"]=="fig-test"

def test_invalid_export_and_manifest(tmp_path):
    fig,ax=plt.subplots()
    with pytest.raises(ValueError): finalize_figure(fig,tmp_path/"x",formats=["exe"])
    with pytest.raises(ValueError): finalize_figure(fig,tmp_path/"x",formats=["png","png"])
    with pytest.raises(ValueError): finalize_figure(fig,tmp_path/"x",dpi=40)
    with pytest.raises(FileNotFoundError):
        build_manifest(contract=contract(),source_files=[tmp_path/"missing.txt"])
    with pytest.raises(ValueError):
        FigureContract("","heatmap","x","source","x","y")
    plt.close(fig)
