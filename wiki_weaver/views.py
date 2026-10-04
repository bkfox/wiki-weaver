from __future__ import annotations

from abc import ABC, abstractmethod
import json
from pathlib import Path
from typing import Any, Generator

from jinja2 import Environment
from pydantic import BaseModel

from .models import Property, Model
from .registry import ContentRegistry, ResolvedModel
from .rendering import RenderContext, RenderedContent


__all__ = (
    "View",
    "ModelPropertyView",
    "ModelWikiCategoryView",
    "ModelWikiTemplateView",
    "ModelWikiFormView",
    "TextView",
    "CssView",
    "PageView",
)


class View(ABC):
    name: str | None = None
    dest: Path | None = None

    def __init__(self, name: str | None = None, dest: Path | None = None):
        if name:
            self.name = name
        self.dest = dest

    @property
    @abstractmethod
    def title(self) -> str: ...

    def get_context(self, render_context) -> dict[str, Any]:
        return {"view": self}

    def render(self, render_context: RenderContext) -> RenderedContent:
        return RenderedContent(
            title=self.title,
            content=self.get_content(render_context),
            path=self.get_dest(render_context),
        )

    @abstractmethod
    def get_content(self, render_context: RenderContext) -> str: ...

    def get_source(self, render_context: RenderContext) -> Path | None:
        return None

    def get_dest(self, render_context: RenderContext) -> Path | None:
        """Return destination path to which the rendered content shall be written."""
        return self.dest


class TemplateView(View):
    template_name: str

    def get_content(self, render_context: RenderContext) -> RenderedContent:
        return self.render_template(render_context)

    def render_template(self, render_context: RenderContext) -> RenderedContent:
        env = self.get_environment(render_context)
        template = env.get_template(self.template_name)
        return template.render(**self.get_context(render_context))

    def get_source(self, render_context: RenderContext) -> Path | None:
        if self.template_name:
            env = self.get_environment(render_context)
            return env.get_template(self.template_name).filename
        return super().get_source(render_context)

    def get_environment(self, render_context: RenderContext) -> Environment:
        return render_context.template_env


class TitledView(View):
    def __init__(self, title: str, **kwargs):
        self._title = title
        super().__init__(**kwargs)

    @property
    def title(self) -> str:
        return self._title


class TextView(TitledView):
    def __init__(self, title: str, content: str = "", **kwargs):
        self.content = content
        super().__init__(title, **kwargs)

    def get_content(self, render_context):
        return self.content


class JsonView(TitledView):
    def __init__(
        self,
        title,
        data: BaseModel | dict | list | None,
        dest: Path | None = None,
        **kwargs,
    ):
        self.data = data
        super().__init__(title, **kwargs)

    def get_content(self, render_context):
        data = self.get_data(render_context)
        if isinstance(data, BaseModel):
            data = data.model_dump(mode="json")
        return json.dumps(data)

    def get_data(self, render_context):
        return self.data


class FileView(TextView):
    path: Path

    def __init__(self, title: str, path: Path, **kwargs):
        super().__init__(title, **kwargs)
        self.path = path

    def get_content(self, render_context):
        if self.path:
            return self.render_file(render_context)
        return super().get_content(render_context)

    def render_file(self, render_context):
        return self.path.read_text(encoding="utf-8")

    def get_source(self, render_context):
        if self.path:
            return self.path
        return super().get_source(render_context)


# ---- Model & properties
class ModelPropertyView(TemplateView):
    name = "property"
    template_name = "property.wiki.j2"

    def __init__(
        self,
        property_name: str,
        property: Property,
        registry: ContentRegistry,
        **kwargs,
    ):
        self.property_name = property_name
        self.property = property
        self.registry = registry
        super().__init__(**kwargs)

    @property
    def title(self) -> str:
        return f"Property:{self.property_name}"

    def get_context(self, render_context) -> dict[str, Any]:
        enumeration = (
            self.registry.get_enum(self.property.enum) if self.property.enum else None
        )

        return {
            **super().get_context(render_context),
            "name": self.property_name,
            "property": self.property,
            "enumeration": enumeration,
        }


class ModelView(View):
    name = "model"

    def __init__(self, model: Model, **kwargs):
        self.model = model
        super().__init__(**kwargs)

    def get_context(self, render_context) -> dict[str, Any]:
        return {
            **super().get_context(render_context),
            "model": self.model,
        }


class ModelPropertiesView(ModelView):
    name = "model_property"

    def get_context(self, render_context):
        properties = {
            name: self.get_property_context(name, property)
            for name, property in self.model.properties.items()
        }

        return {
            **super().get_context(render_context),
            "properties": properties,
            "groups": [
                {
                    "name": name,
                    "label": group.label,
                    "properties": [
                        properties[property_name]
                        for property_name in group.properties
                        if property_name in properties
                    ],
                }
                for name, group in self.model.groups.items()
            ],
            "infobox": [
                {
                    "name": name,
                    "label": self.model.groups[name].label,
                    "properties": [
                        properties[property_name]
                        for property_name in self.model.groups[name].properties
                        if property_name in properties
                    ],
                }
                for name in self.model.infobox.groups
                if name in self.model.groups
            ],
        }

    def get_property_context(self, name: str, property: Property) -> dict[str, Any]:
        return {
            "name": name,
            "label": property.label,
            "property": property,
            "description": property.description,
        }


class ModelWikiCategoryView(ModelView, TemplateView):
    name = "category"
    template_name = "category.wiki.j2"

    @property
    def title(self) -> str:
        return f"Category:{self.model.category.name}"


class ModelWikiTemplateView(ModelPropertiesView, TemplateView):
    name = "template"
    template_name = "template.wiki.j2"

    @property
    def title(self) -> str:
        return f"Template:{self.model.name}"


class ModelWikiFormView(ModelPropertiesView, TemplateView):
    name = "form"
    template_name = "form.wiki.j2"

    def __init__(self, model: ResolvedModel, registry: ContentRegistry, **kwargs):
        super().__init__(model, **kwargs)
        self.registry = registry

    @property
    def title(self) -> str:
        return f"Form:{self.model.name}"

    def get_context(self, render_context) -> dict[str, Any]:
        context = super().get_context(render_context)
        context["for_template"] = self.model.name
        return context

    def get_property_context(
        self,
        name: str,
        property: Property,
    ) -> dict[str, Any]:
        context = super().get_property_context(
            name,
            property,
        )

        context["enumeration"] = (
            self.registry.get_enum(property.enum) if property.enum else None
        )
        context["target_category"] = (
            self.registry.get_model_category(property.target)
            if property.type == "Page"
            and isinstance(property.target, str)
            and property.target != "File"
            else None
        )

        return context


class ModelsJsonView(JsonView):
    name = "models-json"

    def get_dest(self, render_context):
        dest_dir = render_context.static_dest
        dest_dir.mkdir(exist_ok=True)
        return dest_dir / "models.js"

    def get_data(self, render_context):
        return [self.get_model_data(model) for model in self.data]

    def get_model_data(self, model):
        return {
            "name": model.name,
            "label": model.label,
            "description": model.description,
            "data": model.data,
            "properties": {
                k: v.model_dump(mode="json") for k, v in model.properties.items()
            },
        }

    def get_content(self, resolved_models):
        data = super().get_content(resolved_models)
        return f"weaverModels={data}"


# ---- Other views
class CssView(FileView):
    name = "css"


class PageView(FileView, TemplateView):
    name = "page"

    def __init__(
        self, title: str, template_name: str | None, path: str | None = None, **kwargs
    ):
        super().__init__(title, path, **kwargs)
        self.template_name = template_name

    @classmethod
    def from_dir(cls, root: Path, **kwargs) -> Generator[PageView]:
        if not root.exists():
            return

        for path in root.glob("**/*.wiki"):
            yield cls.from_file(root, path, **kwargs)

        for path in root.glob("**/*.wiki.j2"):
            yield cls.from_file(root, path, **kwargs)

    @classmethod
    def from_file(cls, root: Path, path: Path, title=None, **kwargs) -> PageView:
        title = title or cls._page_title(root, path)

        if path.suffix == ".j2":
            template_name, path_ = path.relative_to(root).as_posix(), None
        else:
            template_name, path_ = None, path

        return cls(title=title, template_name=template_name, path=path_)

    @staticmethod
    def _page_title(root: Path, path: Path) -> str:
        relative = path.relative_to(root)
        parts = relative.parts

        if parts[0].startswith("@"):
            namespace, parts = parts[0][1:], parts[1:]
        else:
            namespace = None

        title_path = Path(*parts)
        title = title_path.with_suffix("").with_suffix("").as_posix()
        if namespace:
            return f"{namespace}:{title}"
        return title

    def get_content(self, render_context: RenderContext) -> RenderedContent:
        if self.path:
            return self.render_file(render_context)
        return self.render_template(render_context)

    def get_environment(self, render_context: RenderContext) -> Environment:
        return render_context.page_env
