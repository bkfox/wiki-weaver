from collections.abc import Iterable
from pathlib import Path
import subprocess

from rich import print

from .registry import ContentRegistry, ResolvedModel
from .rendering import RenderedContent, RenderContext
from .lock import RunInfo
from .views import (
    ModelWikiCategoryView,
    ModelWikiFormView,
    ModelPropertyView,
    ModelWikiTemplateView,
    ModelsJsonView,
    CssView,
    PageView,
    View,
)


class MediaWikiImporter:
    css_path = Path("styles/Common.css")
    template_dir = Path("templates")
    page_dir = Path("pages")
    static_dest = Path("resources/assets/wiki-weaver")

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
        """ Weaver sources directory. """
        self.mediawiki = mediawiki
        """ MediaWiki installation directory. """
        self.registry = registry
        """ Data types registry. """
        self.dry_run = dry_run
        self.context = self.get_context()
        self.run_info = run_info
        self.update = update

    def get_context(self) -> RenderContext:
        extra = self.source / "jinja"
        return RenderContext.from_directories(
            template_dir=[self.source / self.template_dir, extra],
            page_dir=[self.source / self.page_dir, extra],
            static_dest=self.mediawiki / self.static_dest,
        )

    def import_all(self, view_names: list[str] | None = None) -> None:
        """
        Import all pages into mediawiki using :py:meth:`views`.

        :param view_names: select views to import by name
        """
        try:
            for view in self.views():
                if not view_names or view.name in view_names:
                    self.import_view(view)
            self.postImport()

            self.command(
                "eval",
                input="""
            $services = MediaWiki\\MediaWikiServices::getInstance();
            $services->getResourceLoader()->clearCache();
            """,
                text=True,
            )
            # self.command("purgeList", "--namespace", "MediaWiki:Common.css")
        except Exception:
            import traceback

            traceback.print_exc()

    def views(self, resolved_models: ResolvedModel | None = None) -> Iterable[View]:
        """
        Yield all views that generate pages to import into MediaWiki.

        It will yield:

            - ModelPropertyView for all properties
            - Different views for resolved models
            - CSS view if a :py:attr:`css_path` is provided and file exists
            - Page from context's ``page_dir``.

        :param resolved_models: if provided use those resolved models instead of registry's ones.
        :yield View: the views to import.
        """
        yield from (
            ModelPropertyView(name, property, self.registry)
            for name, property in self.registry.properties.items()
        )

        if resolved_models is None:
            resolved_models = self.registry.resolve_models()

        yield ModelsJsonView("Models:JSON", resolved_models)

        for model in resolved_models:
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
        print(f"[bold]{view.name}: [yellow]{view.title}[/yellow][/bold]")

        if self.run_info and self.update:
            if not self.run_info.shall_sync(view.title):
                print(" > File not updated: skip")
                return

        print("> Render")
        content = view.render(self.context)
        if dest := content.path:
            print(f"> Write to `{dest}`")
            content.path.write_text(content.content, encoding="utf-8")
        else:
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
