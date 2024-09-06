from pathlib import Path
from typing import Optional

from sphinx_ape._utils import get_package_name


class Documentation:
    def __init__(self, base_path: Optional[Path] = None, name: Optional[str] = None) -> None:
        self._base_path = base_path or Path.cwd()
        self._name = name or get_package_name()

    @property
    def docs_path(self) -> Path:
        return self._base_path / "docs"

    @property
    def build_path(self) -> Path:
        return self.docs_path / "_build" / self._name

    @property
    def latest_path(self) -> Path:
        return self.build_path / "latest"

    @property
    def stable_path(self) -> Path:
        return self.build_path / "stable"

    @property
    def userguides_path(self) -> Path:
        return self.docs_path / "userguides"

    @property
    def commands_path(self) -> Path:
        return self.docs_path / "commands"

    @property
    def methoddocs_path(self) -> Path:
        return self.docs_path / "methoddocs"

    @property
    def conf_file(self) -> Path:
        return self.docs_path / "conf.py"

    @property
    def index_file(self) -> Path:
        return self.build_path / "index.html"

    def init(self):
        if not self.docs_path.is_dir():
            self.docs_path.mkdir()

        self._ensure_quickstart_exists()
        self._ensure_conf_exists()
        self._ensure_index_exists()

    def _ensure_conf_exists(self):
        if self.conf_file.is_file():
            return

        content = 'extensions = ["sphinx_ape"]\n'
        self.conf_file.write_text(content)

    def _ensure_index_exists(self):
        index_file = self.docs_path / "index.rst"
        if index_file.is_file():
            return

        content = ".. dynamic-toc-tree::\n"
        index_file.write_text(content)

    def _ensure_quickstart_exists(self):
        quickstart_path = self.userguides_path / "quickstart.md"
        if quickstart_path.is_file():
            # Already exists.
            return

        self.userguides_path.mkdir(exist_ok=True)
        quickstart_path.write_text("```{include} ../../README.md\n```\n")

    @property
    def userguide_names(self) -> list[str]:
        guides = self._get_filenames(self.userguides_path)
        quickstart_name = "userguides/quickstart"
        if quickstart_name in guides:
            # Make sure quick start is first.
            guides = [quickstart_name, *[g for g in guides if g != quickstart_name]]

        return guides

    @property
    def cli_reference_names(self) -> list[str]:
        return self._get_filenames(self.commands_path)

    @property
    def methoddoc_names(self) -> list[str]:
        return self._get_filenames(self.methoddocs_path)

    def _get_filenames(self, path: Path) -> list[str]:
        if not path.is_dir():
            return []

        return sorted([g.stem for g in path.iterdir() if g.suffix in (".md", ".rst")])
