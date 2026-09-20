from wiki_weaver.registry import ContentRegistry
from wiki_weaver.renderer import WikiRenderer
from wiki_weaver.views import (
    CategoryView,
    FormView,
    PropertyView,
    TemplateView,
)


def test_render_property(
    registry: ContentRegistry,
    templates_directory,
):
    renderer = WikiRenderer(templates_directory)

    property = registry.properties["name"]

    result = renderer.render(
        PropertyView(
            "name",
            property,
            registry,
        ),
    )

    assert result.title == "Property:name"
    assert "[[Has type::Text]]" in result.content
    assert "[[Has preferred property label::Nom@fr]]" in result.content
    assert (
        "[[Has property description::Nom de l'élément.@fr]]"
        in result.content
    )


def test_render_enum_property(
    registry: ContentRegistry,
    templates_directory,
):
    renderer = WikiRenderer(templates_directory)

    model = registry.get_model("Project")
    property = model.properties["projectType"]
    enumeration = registry.get_enum("projectType")

    result = renderer.render(
        PropertyView(
            "projectType",
            property,
            registry,
        ),
    )

    assert result.title == "Property:projectType"
    assert "[[Has type::Text]]" in result.content
    assert (
        "[[Has preferred property label::Type de projet@fr]]"
        in result.content
    )

    for key in enumeration.values:
        assert f"[[Allows value::{key}]]" in result.content


def test_render_category(
    registry: ContentRegistry,
    templates_directory,
):
    renderer = WikiRenderer(templates_directory)
    model = registry.get_model("Project")
    result = renderer.render(CategoryView(model))

    assert result.title == "Category:Projects"
    assert result.content.strip() == model.description


def test_render_template(
    registry: ContentRegistry,
    templates_directory,
):
    renderer = WikiRenderer(templates_directory)
    model = registry.get_model("Project")
    result = renderer.render(TemplateView(model))

    assert result.title == "Template:Project"
    assert "{{{name|}}}" in result.content
    assert "[[name::{{{name|}}}]]" in result.content
    assert "{{{projectType|}}}" in result.content
    assert "[[projectType::{{{projectType|}}}]]" in result.content
    assert "[[Category:Projects]]" in result.content


def test_render_form(
    registry: ContentRegistry,
    templates_directory,
):
    renderer = WikiRenderer(templates_directory)
    model = registry.get_model("Project")
    result = renderer.render(FormView(model, registry))

    assert result.title == "Form:Project"
    assert "{{{for template|Project}}}" in result.content
    assert "{{{end template}}}" in result.content
    assert "{{{field|name|label=Nom|mandatory}}}" in result.content
    assert "input type=dropdown" in result.content

    for key, value in registry.get_enum("projectType").values.items():
        assert f"{key}={value.label}" in result.content

    assert "{{{standard input|save}}}" in result.content
    assert "{{{standard input|cancel}}}" in result.content
