"""Legacy adapters must preserve source numbers and record original files."""
import json
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_three_case_studies_render_and_have_source_hashes(tmp_path):
    spec=importlib.util.spec_from_file_location("migrate_legacy",ROOT/"examples"/"migrate_legacy.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    all_results=module.run_all(tmp_path)
    assert set(all_results)=={"immunostruct_means","macl_pubmedqa","rnagenscape_success"}
    for key,(paths,issues) in all_results.items():
        assert len(paths)==3 and all(p.stat().st_size>32 for p in paths)
        manifest=json.loads((tmp_path/(key+".manifest.json")).read_text(encoding="utf-8"))
        assert manifest["sources"]
        assert all(len(v["sha256"])==64 for v in manifest["sources"])
        assert manifest["figure_contract"]["uncertainty_kind"]=="none"
        assert isinstance(issues,list)
