from wiki_weaver.registry import ContentRegistry


def test_loads_properties(registry: ContentRegistry):
    assert "name" in registry.properties
    assert "description" in registry.properties
    assert "topic" in registry.properties


def test_loads_groups(registry: ContentRegistry):
    assert "identification" in registry.groups
    assert "relations" in registry.groups


def test_loads_models(registry: ContentRegistry):
    assert "Place" in registry.models
    assert "Territory" in registry.models
    assert "Organization" in registry.models
    assert "Person" in registry.models
    assert "Project" in registry.models
    assert "Event" in registry.models


def test_loads_enumerations(registry: ContentRegistry):
    assert "projectType" in registry.enums

    enumeration = registry.enums["projectType"]

    assert enumeration.values
    assert all(
        isinstance(value.label, str)
        for value in enumeration.values.values()
    )


def test_property_definition(registry: ContentRegistry):
    property = registry.properties["name"]

    assert property.type == "Text"
    assert property.label == "Nom"
    assert property.required is True
    assert property.multiple is False


def test_model_property_definition(registry: ContentRegistry):
    model = registry.models["Project"]

    assert "projectType" in model.properties

    property = model.properties["projectType"]

    assert property.type == "Text"
    assert property.enum == "projectType"


def test_page_model_property_definition(registry: ContentRegistry):
    model = registry.models["Project"]

    assert "leadOrganization" in model.properties

    property = model.properties["leadOrganization"]

    assert property.type == "Page"
    assert property.target == "Organization"
