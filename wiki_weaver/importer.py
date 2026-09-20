from collections.abc import Iterable
from pathlib import Path
import subprocess

from rich import print

from .registry import ContentRegistry
from .rendering import RenderedContent, RenderContext
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
    ):
        self.source = source
        self.mediawiki = mediawiki
        self.registry = registry
        self.dry_run = dry_run
        self.context = self.get_context()
        breakpoint()

    def get_context(self) -> RenderContext:
        return RenderContext.from_directories(
            template_dir=self.source / self.template_dir,
            page_dir=self.source / self.page_dir
        )

    def import_all(self, view_names: list[str]|None=None) -> None:
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

        for dir in self.context.page_dir:
            for page in PageView.from_dir(dir):
                yield page

    def import_view(self, view: View) -> None:
        attrs = {
            k: getattr(view, k)
                for k in ("model",) if hasattr(view, k)
        }
        attrs = ', '.join(f"{k}={v.name}" for k, v in attrs.items())
        print(f"[bold]{view.__class__.__name__}: [yellow]{view.title}[/yellow][/bold]")
        content = view.render(self.context)
        self._edit(content)
        print("")

    def _edit(self, content: RenderedContent) -> None:
        if self.dry_run:
            print(f"\n===== {content.title} =====")
            print(content.content)
            return

        self.command("edit", "-u", "ContentImporter", "-b", "-s", "Update content definition", content.title, input=content.content)

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
