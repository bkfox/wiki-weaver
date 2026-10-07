from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


PropertyType = Literal[
    "Text",
    "Page",
    "Date",
    "URL",
    "Geographic coordinate",
    "Number",
    "Boolean",
]


class EnumValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str


class Enumeration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    values: dict[str, EnumValue]


class PropertyInput(BaseModel):
    """Page Form input."""

    type: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class Property(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: PropertyType
    label: str
    description: str | None = None
    required: bool = False
    multiple: bool = False
    target: str | list[str] | None = None
    enum: str | None = None
    input: PropertyInput | None = None

    @model_validator(mode="after")
    def validate_definition(self) -> Property:
        if self.type != "Page" and self.target is not None:
            raise ValueError("'target' can only be used with properties of type 'Page'")

        if self.type == "Page" and self.enum is not None:
            raise ValueError("'enum' cannot be used with properties of type 'Page'")

        return self


class PropertyGroup(BaseModel):
    label: str
    properties: list[str]


class PropertyFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    groups: dict[str, PropertyGroup] = Field(default_factory=dict)
    properties: dict[str, Property] = Field(default_factory=dict)


class Infobox(BaseModel):
    groups: list[str] = Field(default_factory=list)


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    """ Canonical name. """
    label: str
    """ Displayed name. """
    description: str | None = None
    """ Description. """
    groups: list[str] = Field(default_factory=list)
    """ Property groups this model has. """
    properties: dict[str, Property] = Field(default_factory=dict)
    """ Extra properties. """
    mdi_icon: str | None = None
    """ MDI icon. """
    infobox: Infobox = Field(default_factory=Infobox)
    """ Groups displayed in the infobox. """
    data: dict[str, Any] = Field(default_factory=dict)


class ModelFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: Model


class ContentDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enums: dict[str, Enumeration] = Field(default_factory=dict)
