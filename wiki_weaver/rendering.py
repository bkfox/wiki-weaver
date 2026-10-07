from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


@dataclass(frozen=True)
class RenderedContent:
    """Content returned by a view."""

    title: str
    content: str
    path: Path | None = None
    """
    Target file path where to write the content.

    When not provided, the importer actually import into the MediaWiki database.
    When provided, it will instead write the file at this place.
    """


@dataclass(frozen=True)
class RenderContext:
    template_env: Environment
    page_env: Environment
    static_dest: Path

    _root_template = Path(__file__).parent.parent / "data" / "templates"

    @classmethod
    def from_directories(
        cls, template_dir: Path, page_dir: Path, **kwargs
    ) -> RenderContext:
        if isinstance(template_dir, (str, Path)):
            template_dir = [template_dir, cls._root_template]
        else:
            template_dir = [*template_dir, cls._root_template]

        return cls(
            template_env=cls._create_environment(template_dir),
            page_env=cls._create_environment(page_dir),
            **kwargs,
        )

    @staticmethod
    def _create_environment(directory: Path) -> Environment:
        return Environment(
            loader=FileSystemLoader(directory),
            undefined=StrictUndefined,
            autoescape=False,
            keep_trailing_newline=True,
        )

    @cached_property
    def template_dir(self) -> list[Path]:
        return [Path(p) for p in self.template_env.loader.searchpath]

    @cached_property
    def page_dir(self) -> list[Path]:
        return [Path(p) for p in self.page_env.loader.searchpath]
