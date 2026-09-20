import pytest

from wiki_weaver.registry import ContentRegistry, ResolvedModel


def test_registry_validates(registry: ContentRegistry):
    registry.validate()


def test_resolve_models(registry: ContentRegistry):
    models = registry.resolve_models()

    assert models
    assert all(isinstance(model, ResolvedModel) for model in models)

    names = {model.name for model in models}

    assert "Place" in names
    assert "Project" in names
    assert "Event" in names


def test_get_model_returns_resolved_model(registry: ContentRegistry):
    model = registry.get_model("Project")

    assert isinstance(model, ResolvedModel)

    assert model.name == "Project"
    assert model.label == "Projet"
    assert model.category.name == "Projects"

    assert "name" in model.properties
    assert "description" in model.properties
    assert "projectType" in model.properties
    assert "leadOrganization" in model.properties


def test_resolved_model_includes_group_properties(
    registry: ContentRegistry,
):
    model = registry.get_model("Project")

    assert "name" in model.properties
    assert "description" in model.properties
    assert "topic" in model.properties
    assert "coordinates" in model.properties
    assert "dateStart" in model.properties


def test_resolved_model_contains_raw_model(
    registry: ContentRegistry,
):
    model = registry.get_model("Project")

    assert model.model is registry.models["Project"]


def test_get_enum(registry: ContentRegistry):
    enumeration = registry.get_enum("projectType")

    assert enumeration.label
    assert enumeration.values

    for key, value in enumeration.values.items():
        assert key
        assert value.label


def test_get_unknown_enum(registry: ContentRegistry):
    with pytest.raises(ValueError, match="Unknown enumeration"):
        registry.get_enum("doesNotExist")


def test_get_model(registry: ContentRegistry):
    model = registry.get_model("Project")

    assert model.name == "Project"


def test_get_unknown_model(registry: ContentRegistry):
    with pytest.raises(ValueError, match="Unknown model"):
        registry.get_model("DoesNotExist")


def test_get_model_category(registry: ContentRegistry):
    assert registry.get_model_category("Project") == "Projects"
