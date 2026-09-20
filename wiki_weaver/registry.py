from __future__ import annotations

from dataclasses import dataclass

from .models import Enumeration, Model, Property


@dataclass(frozen=True)
class ResolvedModel:
    model: Model
    properties: dict[str, Property]
    groups: dict[str, list[str]]

    def __getattr__(self, key: str):
        return getattr(self.model, key)


class ContentRegistry:
    """Validate and resolve the complete content definition."""

    def __init__(
        self,
        properties: dict[str, Property],
        groups: dict[str, PropertyGroup],
        models: dict[str, Model],
        enums: dict[str, Enumeration],
    ) -> None:
        self.properties = properties
        self.groups = groups
        self.models = models
        self.enums = enums

    def validate(self) -> None:
        self._validate_groups()
        self._validate_properties()
        self._validate_models()

    def resolve_models(self) -> list[ResolvedModel]:
        return [
            self.get_model(name)
            for name in self.models
        ]

    def get_enum(self, name: str) -> Enumeration:
        try:
            return self.enums[name]
        except KeyError:
            raise ValueError(f"Unknown enumeration: {name}")

    def get_model(self, name: str) -> ResolvedModel:
        try:
            model = self.models[name]
        except KeyError:
            raise ValueError(f"Unknown model: {name}")

        groups = {
            group_name: self.groups[group_name]
            for group_name in model.groups
        }
        return ResolvedModel(
            model=model,
            properties=self._resolve_model_properties(model),
            groups=groups
        )

    def get_model_category(self, name: str) -> str:
        return self.get_model(name).category.name

    def _validate_groups(self) -> None:
        for group_name, group in self.groups.items():
            for property_name in group.properties:
                if property_name not in self.properties:
                    raise ValueError(
                        f"Group '{group_name}' references unknown "
                        f"property '{property_name}'"
                    )

    def _validate_properties(self) -> None:
        model_names = set(self.models)

        for name, prop in self.properties.items():
            self._validate_property(
                name,
                prop,
                model_names,
            )

    def _validate_models(self) -> None:
        for model in self.models.values():
            for group_name in model.groups:
                if group_name not in self.groups:
                    raise ValueError(
                        f"Model '{model.name}' references unknown "
                        f"group '{group_name}'"
                    )

            for property_name, prop in model.properties.items():
                self._validate_property(
                    property_name,
                    prop,
                    set(self.models),
                )

    def _validate_property(
        self,
        name: str,
        prop: Property,
        model_names: set[str],
    ) -> None:
        if prop.enum is not None:
            if prop.enum not in self.enums:
                raise ValueError(
                    f"Property '{name}' references unknown "
                    f"enumeration '{prop.enum}'"
                )

        if prop.type != "Page":
            return

        targets = prop.target

        if targets is None:
            return

        if isinstance(targets, str):
            targets = [targets]

        for target in targets:
            if target not in model_names and target != "File":
                raise ValueError(
                    f"Property '{name}' references unknown "
                    f"target model '{target}'"
                )

    def _resolve_model_properties(
        self,
        model: Model,
    ) -> dict[str, Property]:
        properties: dict[str, Property] = {}

        for group_name in model.groups:
            for property_name in self.groups[group_name].properties:
                self._add_property(
                    properties,
                    property_name,
                    self.properties[property_name],
                    model.name,
                )

        for property_name, prop in model.properties.items():
            self._add_property(
                properties,
                property_name,
                prop,
                model.name,
            )

        return properties

    def _add_property(
        self,
        destination: dict[str, Property],
        name: str,
        prop: Property,
        model_name: str,
    ) -> None:
        if name in destination:
            existing = destination[name]

            if existing != prop:
                raise ValueError(
                    f"Model '{model_name}' defines property '{name}' "
                    "more than once with different definitions"
                )

            return

        destination[name] = prop
