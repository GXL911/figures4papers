"""Run all four synthetic templates; safe with or without editable install."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run_all(output_dir: Path):
    results={}
    for name in ("grouped_bar","learning_curves","heatmap","reliability_diagram"):
        spec=spec_from_file_location(name,ROOT/"templates"/f"{name}.py")
        mod=module_from_spec(spec)
        spec.loader.exec_module(mod)
        paths,issues=mod.build(output_dir)
        results[name]=paths
        print(f"{name}: {len(paths)} exports; {len(issues)} diagnostic warnings")
        for issue in issues:
            print(f"  [{issue.level}] {issue.code}: {issue.message}")
    return results

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=ROOT/"examples"/"generated")
    args=parser.parse_args()
    run_all(args.out)
