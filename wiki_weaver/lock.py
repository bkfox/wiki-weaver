from datetime import datetime, UTC
from pathlib import Path

from pydantic import BaseModel, Field

from .files import read_json, write_json


class PageInfo(BaseModel):
    view: str
    path: Path | None = None
    synced: datetime | None = None
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RunInfo(BaseModel):
    source: Path
    target: Path
    runned: datetime | None = None
    pages: dict[str, PageInfo] = Field(default_factory=dict)

    def shall_sync(self, title) -> bool:
        page = self.pages.get(title)
        if not page or not page.path or not page.path.exists() or not self.synced:
            return True
        return page.path.stat().st_mtime > page.synced.timestamp()

    def runned_now(self):
        self.runned = datetime.now(UTC)

    def synced(self, title, **kwargs) -> PageInfo:
        kwargs["synced"] = datetime.now(UTC)

        page = self.pages.get(title)
        if not page:
            page = PageInfo(**kwargs)
            self.pages[title] = page
        else:
            for k, v in kwargs.items():
                setattr(page, k, v)
        return page


class LockFile(BaseModel):
    updated: datetime | None = None
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    runs: list[RunInfo] = Field(default_factory=list)

    def updated_now(self):
        self.updated = datetime.now(UTC)

    # TODO: move out
    @classmethod
    def load(cls, path: Path, allow_create: bool = True):
        if not path.exists():
            if not allow_create:
                raise FileNotFoundError(f"File does not exists: {path}")

            return LockFile()
        return read_json(path, cls)

    def save(self, path: Path):
        write_json(path, self)

    def get_or_create_run(self, source, target):
        breakpoint()
        run = next(
            (r for r in self.runs if r.source == source and r.target == target), None
        )
        if not run:
            run = RunInfo(source=source, target=target)
            self.runs.append(run)
        return run
