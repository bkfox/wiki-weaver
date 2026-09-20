from collections.abc import Iterable
from pathlib import Path
import subprocess

from rich import print

from .registry import ContentRegistry
from .rendering import RenderedContent, RenderContext
from .lock import RunInfo
from .views import (
    ModelWikiCategoryView,
    ModelWikiFormView,
    ModelPropertyView,
    ModelWikiTemplateView,
    CssView,
    PageView,
    View,
)


class MediaWikiImporter:
    css_path = Path("styles/Common.css")
    template_dir = Path("templates")
    page_dir = Path("pages")

    def __init__(
        self,
        source: Path,
        mediawiki: Path,
        registry: ContentRegistry,
        dry_run: bool = False,
        run_info: RunInfo | None = None,
        update: bool = False,
    ):
        self.source = source
        self.mediawiki = mediawiki
        self.registry = registry
        self.dry_run = dry_run
        self.context = self.get_context()
        self.run_info = run_info
        self.update = update

    def get_context(self) -> RenderContext:
        extra = self.source / "jinja"
        return RenderContext.from_directories(
            template_dir=[self.source / self.template_dir, extra],
            page_dir=[self.source / self.page_dir, extra],
        )

    def import_all(self, view_names: list[str] | None = None) -> None:
        try:
            for view in self.views():
                if not view_names or view.name in view_names:
                    self.import_view(view)
            self.postImport()
        except Exception:
            import traceback

            traceback.print_exc()

    def views(self) -> Iterable[View]:
        yield from (
            ModelPropertyView(name, property, self.registry)
            for name, property in self.registry.properties.items()
        )

        for model in self.registry.resolve_models():
            yield ModelWikiCategoryView(model)
            yield ModelWikiTemplateView(model)
            yield ModelWikiFormView(model, self.registry)

        css_path = self.source / self.css_path
        if css_path.exists():
            yield CssView("MediaWiki:Common.css", css_path)

        # We only run over the first item because other are utilities not used for import.
        for page in PageView.from_dir(self.context.page_dir[0]):
            yield page

    def import_view(self, view: View) -> None:
        print(f"[bold]{view.__class__.__name__}: [yellow]{view.title}[/yellow][/bold]")

        if self.run_info and self.update:
            breakpoint()
            if not self.run_info.shall_sync(view.title):
                print(" > File not updated: skip")
                return

        print("> Render")
        content = view.render(self.context)
        print("> Synchronize")
        self._edit(content)
        if self.run_info and not self.dry_run:
            self.run_info.synced(
                view.title, view=view.name, path=view.get_source(self.context)
            )
        print("")

    def _edit(self, content: RenderedContent) -> None:
        if self.dry_run:
            print(f"\n===== {content.title} =====")
            print(content.content)
            return

        self.command(
            "edit",
            "-u",
            "ContentImporter",
            "-b",
            "-s",
            "Update content definition",
            content.title,
            input=content.content,
        )

    def postImport(self):
        self.command("runJobs")

    def command(self, name, *args, **kwargs):
        return self.shell(["php", "maintenance/run.php", name, *args], **kwargs)

    def shell(self, command, **kwargs):
        kwargs = {
            "cwd": self.mediawiki,
            "text": True,
            "check": True,
            **kwargs,
        }
        return subprocess.run(command, **kwargs)
