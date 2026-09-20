from pathlib import Path

import pytest

from wiki_weaver.loader import ContentLoader
from wiki_weaver.registry import ContentRegistry


@pytest.fixture
def content_directory() -> Path:
    return Path(__file__).parents[1] / "data"


@pytest.fixture
def templates_directory(content_directory: Path) -> Path:
    return content_directory / "templates"


@pytest.fixture
def content_loader(content_directory: Path) -> ContentLoader:
    return ContentLoader(content_directory)


@pytest.fixture
def registry(content_loader: ContentLoader) -> ContentRegistry:
    properties, groups, models, definition = content_loader.load()

    registry = ContentRegistry(
        properties=properties,
        groups=groups,
        models=models,
        enums=definition.enums,
    )
    registry.validate()

    return registry
