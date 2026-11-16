import json
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_all_four_synthetic_examples(tmp_path):
    for name in ("grouped_bar","learning_curves","heatmap","reliability_diagram"):
        spec=importlib.util.spec_from_file_location(name,ROOT/"templates"/f"{name}.py")
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        paths,issues=module.build(tmp_path/name)
        assert len(paths)==3
        assert all(p.stat().st_size>32 for p in paths)
        manifest=next((tmp_path/name).glob("*.manifest.json"))
        data=json.loads(manifest.read_text(encoding="utf-8"))
        assert "synthetic" in data["figure_contract"]["source_description"].lower()
        assert isinstance(issues,list)
