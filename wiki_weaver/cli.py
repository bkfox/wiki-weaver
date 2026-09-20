from __future__ import annotations

import inspect
from pathlib import Path

import click

from . import views
from .lock import LockFile
from .importer import MediaWikiImporter
from .loader import ContentLoader
from .registry import ContentRegistry


views = {
    v.name: v
    for k, v in vars(views).items()
    if inspect.isclass(v) and issubclass(v, views.View) and v.name
}


@click.command()
@click.option(
    "--target",
    "-t",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True, exists=True),
    required=True,
    help="MediaWiki installation directory.",
)
@click.option(
    "--source",
    "-s",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True, exists=True),
    required=True,
    help="Directory containing the content YAML files.",
)
@click.option(
    "--view",
    "-v",
    multiple=True,
    type=click.Choice(views.keys()),
    help="Select one or more views to render",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate and render pages without importing them.",
)
@click.option("--update", "-u", is_flag=True, help="Synchronize only updated files.")
@click.option(
    "--lock",
    type=click.Path(path_type=Path, file_okay=True, dir_okay=False),
    default=Path("wiki-weaver.lock"),
    help="Path to lock file.",
)
def main(
    target: Path,
    source: Path,
    view: list[str],
    dry_run: bool,
    lock: Path,
    update: bool,
) -> None:
    """Update MediaWiki content definitions from YAML."""

    try:
        lock_file = LockFile.load(lock)

        loader = ContentLoader(source)
        properties, groups, models, enum_definition = loader.load()
        registry = ContentRegistry(
            properties=properties,
            groups=groups,
            models=models,
            enums=enum_definition.enums,
        )
        registry.validate()

        importer = MediaWikiImporter(
            source,
            target,
            registry=registry,
            dry_run=dry_run,
            update=update,
            run_info=lock_file.get_or_create_run(source, target),
        )
        if not importer.run_info.runned:
            lock_file.save(lock)

        importer.import_all(view_names=view)
        lock_file.save(lock)

    except (ValueError, FileNotFoundError) as exc:
        import traceback

        traceback.print_exc()
        raise click.ClickException(str(exc)) from exc
