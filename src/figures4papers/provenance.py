"""Content-addressed provenance for generated files and source inputs."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.metadata
from pathlib import Path

from .figure_contract import FigureContract
from ._version import __version__ as SOURCE_VERSION

def file_sha256(path: str | Path) -> str:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def build_manifest(*, contract: FigureContract, source_files=(), output_files=(),
                   seed: int | None = None, transformations=(), metadata=None) -> dict:
    """Record evidence; SHA verifies file identity, not scientific correctness."""
    import matplotlib
    import numpy
    sources = [{"path": str(p), "sha256": file_sha256(p)} for p in source_files]
    outputs = [{"path": str(p), "sha256": file_sha256(p)} for p in output_files]
    if any(not isinstance(s, str) or not s for s in transformations):
        raise ValueError("transformations must be explicit nonblank strings.")
    try:
        package_version = importlib.metadata.version("figures4papers")
    except importlib.metadata.PackageNotFoundError:
        package_version = SOURCE_VERSION
    return {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "figure_contract": contract.to_dict(),
        "sources": sources,
        "outputs": outputs,
        "transformations": list(transformations),
        "random_seed": seed,
        "metadata": dict(metadata or {}),
        "versions": {
            "numpy": numpy.__version__,
            "matplotlib": matplotlib.__version__,
            "figures4papers": package_version,
        },
    }
