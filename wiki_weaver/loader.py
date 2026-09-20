from __future__ import annotations

from pathlib import Path
from typing import Any

from rich import print
import yaml
from pydantic import ValidationError

from .models import (
    ContentDefinition,
    Model,
    ModelFile,
    Property,
    PropertyFile,
    PropertyGroup,
)


__all__ = ("ContentLoader",)


class ContentLoader:
    """Load YAML content definitions from a directory."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self) -> tuple[dict[str, Property], dict[str, PropertyGroup], dict[str, Model], ContentDefinition]:
        property_files = self._find_files("properties")
        model_files = self._find_files("models")

        properties, groups, enums = self._load_properties(property_files)
        models = self._load_models(model_files)

        return properties, groups, models, enums

    def _find_files(self, directory: str) -> list[Path]:
        path = self.root / directory

        if not path.is_dir():
            raise FileNotFoundError(f"Missing content directory: {path}")

        return sorted(path.rglob("*.yaml"))

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)

        if not isinstance(data, dict):
            raise ValueError(f"{path}: root value must be a mapping")

        return data

    def _load_properties(
        self,
        paths: list[Path],
    ) -> tuple[dict[str, Property], dict[str, PropertyGroup], ContentDefinition]:
        properties: dict[str, Property] = {}
        groups: dict[str, list[str]] = {}
        enums: dict[str, Any] = {}

        print("*Load properties...*")

        for path in paths:
            print(f"- `{path}`")
            data = self._read_yaml(path)

            if "enums" in data:
                definition = ContentDefinition.model_validate(data)
                self._merge_enums(enums, definition.enums, path)

            else:
                definition = PropertyFile.model_validate(data)
                self._merge_properties(
                    properties,
                    definition.properties,
                    path,
                )
                self._merge_groups(
                    groups,
                    definition.groups,
                    path,
                )

        return properties, groups, ContentDefinition(enums=enums)

    def _load_models(self, paths: list[Path]) -> dict[str, Model]:
        models: dict[str, Model] = {}

        print("*Load models...*")

        for path in paths:
            try:
                model_file = ModelFile.model_validate(self._read_yaml(path))
            except ValidationError as exc:
                raise ValueError(f"{path}:\n{exc}") from exc

            model = model_file.model
            print(f"- `{path}`: {model.name}")

            if model.name in models:
                raise ValueError(
                    f"{path}: duplicate model '{model.name}'"
                )

            models[model.name] = model

        return models

    def _merge_properties(
        self,
        destination: dict[str, Property],
        source: dict[str, Property],
        path: Path,
    ) -> None:
        for name, value in source.items():
            if name in destination:
                raise ValueError(
                    f"{path}: duplicate property '{name}'"
                )

            destination[name] = value

    def _merge_groups(
        self,
        destination: dict[str, list[str]],
        source: dict[str, list[str]],
        path: Path,
    ) -> None:
        for name, values in source.items():
            if name in destination:
                raise ValueError(
                    f"{path}: duplicate property group '{name}'"
                )

            destination[name] = values

    def _merge_enums(
        self,
        destination: dict[str, Any],
        source: dict[str, Any],
        path: Path,
    ) -> None:
        for name, value in source.items():
            if name in destination:
                raise ValueError(
                    f"{path}: duplicate enumeration '{name}'"
                )

            destination[name] = value
