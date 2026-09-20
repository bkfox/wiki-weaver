from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


@dataclass(frozen=True)
class RenderedContent:
    title: str
    content: str


@dataclass(frozen=True)
class RenderContext:
    template_env: Environment
    page_env: Environment

    @classmethod
    def from_directories(cls, template_dir: Path, page_dir: Path) -> RenderContext:
        return cls(
            template_env=cls._create_environment(template_dir),
            page_env=cls._create_environment(page_dir)
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
