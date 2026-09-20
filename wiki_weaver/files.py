import json
from pathlib import Path
from typing import Any, Type

import yaml
from pydantic import BaseModel


__all__ = ("read_yaml", "read_json", "write_yaml", "write_json")


def read_yaml(
    path: Path, model: Type[BaseModel] | None = None
) -> dict[str, Any] | BaseModel:
    """Read YAML file and deserialize it."""
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)

    if not isinstance(data, dict):
        raise ValueError(f"{path}: root value must be a mapping")

    if model:
        return model.model_validate(data)
    return data


def read_json(
    path: Path, model: Type[BaseModel] | None = None
) -> dict[str, Any] | BaseModel:
    """Read YAML file and deserialize it."""
    with path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)

    if not isinstance(data, dict):
        raise ValueError(f"{path}: root value must be a mapping")

    if model:
        return model.model_validate(data)
    return data


def write_yaml(path: Path, model: BaseModel) -> dict[str, Any] | BaseModel:
    """Read YAML file and deserialize it."""
    with path.open("w", encoding="utf-8") as stream:
        data = model.model_dump(mode="json")
        yaml.dump(data, stream)


def write_json(path: Path, model: BaseModel) -> dict[str, Any] | BaseModel:
    """Read YAML file and deserialize it."""
    with path.open("w", encoding="utf-8") as stream:
        data = model.model_dump(mode="json")
        json.dump(data, stream)
