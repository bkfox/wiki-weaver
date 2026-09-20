from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generator

from .models import Property, Model
from .registry import ContentRegistry
from .rendering import RenderContext, RenderedContent


__all__ = ("View", "ModelPropertyView", "ModelWikiCategoryView", "ModelWikiTemplateView", "ModelWikiFormView", "TextView", "CssView", "PageView")


class View(ABC):
    name: str|None = None

    @property
    @abstractmethod
    def title(self) -> str:
        ...


    def get_context(self, render_context) -> dict[str, Any]:
        return {
            "view": self
        }


    @abstractmethod
    def render(self, render_context: RenderContext) -> RenderedContent:
        ...


class TemplateView(View):
    template_name: str

    def render(self, render_context):
        return self.render_template(render_context)
    
    def render_template(self, render_context: RenderContext) -> RenderedContent:
        env = self.get_environment(render_context)
        template = env.get_template( self.template_name )
        content = template.render( **self.get_context(render_context) )
        return RenderedContent(title=self.title, content=content)

    def get_environment(self, render_context: RenderContext) -> Environment:
        return render_context.template_env


class TextView(View):
    def __init__(self, title: str, content: str=""):
        self._title = title
        self.content = content

    @property
    def title(self) -> str:
        return self._title

    def render(self, render_context: RenderContext) -> RenderedContent:
        return RenderedContent(title=self.title, content=self.content)


class FileView(TextView):
    path: Path

    def __init__(self, title: str, path: Path, **kwargs):
        super().__init__(title, **kwargs)
        self.path = path

    def render(self, render_context):
        if self.path:
            return self.render_file(render_context)
        return super().render(render_context)

    def render_file(self, render_context):
        return RenderedContent(title=self.title, content=self.path.read_text(encoding="utf-8"))


# ---- Model & properties
class ModelPropertyView(TemplateView):
    name = "property"
    template_name = "property.wiki.j2"

    def __init__( self, name: str, property: Property, registry: ContentRegistry):
        self.name = name
        self.property = property
        self.registry = registry

    @property
    def title(self) -> str:
        return f"Property:{self.name}"

    def get_context(self, render_context) -> dict[str, Any]:
        enumeration = (
            self.registry.get_enum(self.property.enum)
            if self.property.enum
            else None
        )

        return {
            **super().get_context(render_context),
            "name": self.name,
            "property": self.property,
            "enumeration": enumeration,
        }


class ModelView(View):
    name = "model"
    
    def __init__(self, model: Model):
        self.model = model

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
            ]
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

    def __init__(
        self,
        model: ResolvedModel,
        registry: ContentRegistry,
    ):
        super().__init__(model)
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
            self.registry.get_enum(property.enum)
            if property.enum
            else None
        )
        context["target_category"] = (
            self.registry.get_model_category(property.target)
            if property.type == "Page"
            and isinstance(property.target, str)
            and property.target != "File"
            else None
        )

        return context


# ---- Other views
class CssView(FileView):
    name = "css"


class PageView(FileView, TemplateView):
    name = "page"

    def __init__(self, title: str, template_name: str|None, path: str|None=None):
        super().__init__(title, path)
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

        return cls(
            title=title,
            template_name=template_name,
            path=path_
        )

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
        
    def render(self, render_context: RenderContext) -> RenderedContent:
        if self.path:
            return self.render_file(render_context)
        return self.render_template(render_context)

    def get_environment(self, render_context: RenderContext) -> Environment:
        return render_context.page_env
