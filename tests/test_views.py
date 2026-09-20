from wiki_weaver.registry import ContentRegistry
from wiki_weaver.views import (
    CategoryView,
    FormView,
    PropertyView,
    TemplateView,
)


def test_property_view(registry: ContentRegistry):
    property = registry.properties["name"]

    view = PropertyView(
        "name",
        property,
        registry,
    )

    assert view.title == "Property:name"

    context = view.get_context()

    assert context["name"] == "name"
    assert context["property"] is property
    assert context["enumeration"] is None


def test_enum_property_view(registry: ContentRegistry):
    model = registry.get_model("Project")
    property = model.properties["projectType"]

    view = PropertyView(
        "projectType",
        property,
        registry,
    )

    assert view.title == "Property:projectType"

    context = view.get_context()

    assert context["enumeration"] is registry.enums["projectType"]


def test_category_view(registry: ContentRegistry):
    model = registry.get_model("Project")

    view = CategoryView(model)

    assert view.title == "Category:Projects"

    context = view.get_context()

    assert context["model"] is model


def test_template_view(registry: ContentRegistry):
    model = registry.get_model("Project")

    view = TemplateView(model)

    assert view.title == "Template:Project"

    context = view.get_context()

    assert context["model"] is model
    assert context["category"] is model.category

    properties = {
        property["name"]: property
        for property in context["properties"]
    }

    assert "name" in properties
    assert "projectType" in properties

    assert properties["name"]["label"] == "Nom"
    assert properties["name"]["parameter"] == "{{{name|}}}"
    assert properties["name"]["semantic"] == "[[name::{{{name|}}}]]"


def test_form_view(registry: ContentRegistry):
    model = registry.get_model("Project")

    view = FormView(model, registry)

    assert view.title == "Form:Project"

    context = view.get_context()

    assert context["model"] is model
    assert context["for_template"] == "{{{for template|Project}}}"
    assert context["end_template"] == "{{{end template}}}"
    assert context["standard_save"] == "{{{standard input|save}}}"
    assert context["standard_cancel"] == "{{{standard input|cancel}}}"


def test_form_view_contains_fields(registry: ContentRegistry):
    model = registry.get_model("Project")

    view = FormView(model, registry)
    context = view.get_context()

    properties = {
        property["name"]: property
        for property in context["properties"]
    }

    assert "name" in properties
    assert "projectType" in properties
    assert "status" in properties
    assert "leadOrganization" in properties

    assert properties["name"]["field"] == (
        "{{{field|name|label=Nom|mandatory}}}"
    )


def test_form_view_enum_field(registry: ContentRegistry):
    model = registry.get_model("Project")

    view = FormView(model, registry)
    context = view.get_context()

    properties = {
        property["name"]: property
        for property in context["properties"]
    }

    field = properties["projectType"]["field"]
    enumeration = registry.get_enum("projectType")

    assert "field|projectType" in field
    assert "label=Type de projet" in field
    assert "input type=dropdown" in field

    for key, value in enumeration.values.items():
        assert f"{key}={value.label}" in field


def test_form_view_page_field(registry: ContentRegistry):
    model = registry.get_model("Project")

    view = FormView(model, registry)
    context = view.get_context()

    properties = {
        property["name"]: property
        for property in context["properties"]
    }

    field = properties["leadOrganization"]["field"]

    assert "field|leadOrganization" in field
    assert "input type=combobox" in field
    assert "values from category=Organizations" in field
