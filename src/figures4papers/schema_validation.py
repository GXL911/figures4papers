"""Load and validate the versioned JSON contracts shipped with the package."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import sysconfig
from typing import Any, Mapping

from jsonschema import Draft202012Validator, ValidationError


class SchemaValidationError(ValueError):
    """A JSON document does not satisfy its published schema."""


def _schema_directory() -> Path:
    source_tree = Path(__file__).resolve().parents[2] / "schemas"
    if source_tree.is_dir():
        return source_tree
    installed = Path(sysconfig.get_path("data")) / "share" / "figures4papers" / "schemas"
    if installed.is_dir():
        return installed
    raise FileNotFoundError("Installed figures4papers JSON Schemas could not be located.")


@lru_cache(maxsize=8)
def load_schema(name: str) -> dict[str, Any]:
    if name not in {"design-brief.schema.json", "scene.schema.json"}:
        raise ValueError(f"Unknown schema document: {name}")
    path = _schema_directory() / name
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"Invalid JSON Schema document {path}: {exc}") from exc
    Draft202012Validator.check_schema(schema)
    return schema


def validate_json_document(instance: Mapping[str, Any], schema_name: str) -> None:
    """Validate one mapping using the declared JSON Schema Draft 2020-12 contract."""
    validator = Draft202012Validator(load_schema(schema_name))
    try:
        validator.validate(instance)
    except ValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        raise SchemaValidationError(f"{schema_name} violation at {location}: {exc.message}") from exc
