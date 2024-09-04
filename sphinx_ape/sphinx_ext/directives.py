from pathlib import Path

from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


class DynamicTocTree(SphinxDirective):
    """
    Dynamically create the TOC-tree so users don't
    need to create and maintain index.html files.
    """

    option_spec = {
        "title": directives.unchanged,
    }

    @property
    def _base_path(self) -> Path:
        env = self.state.document.settings.env
        return Path(env.srcdir)

    @property
    def title(self) -> str:
        if res := self.options.get("title"):
            # User configured the title.
            return res

        # Deduced: "Ape-Docs" or "Ape-Vyper-Docs", etc.
        name = self._base_path.parent.name
        name_parts = [n.capitalize() for n in name.split("-")]
        capped_name = "-".join(name_parts)
        return f"{capped_name}-Docs"

    @property
    def _title_rst(self) -> str:
        title = self.title
        bar = "=" * len(title)
        return f"{title}\n{bar}"

    @property
    def userguides_path(self) -> Path:
        return self._base_path / "userguides"

    @property
    def commands_path(self) -> Path:
        return self._base_path / "commands"

    @property
    def methoddocs_path(self) -> Path:
        return self._base_path / "methoddocs"

    def run(self):
        userguides = self._get_userguides()
        cli_docs = self._get_cli_references()
        methoddocs = self._get_methoddocs()
        plugin_methoddocs = [d for d in methoddocs if d.startswith("ape-")]
        methoddocs = [d for d in methoddocs if d not in plugin_methoddocs]
        sections = {"User Guides": userguides, "CLI Reference": cli_docs}
        if plugin_methoddocs:
            # Core (or alike)
            sections["Plugin Python Reference"] = plugin_methoddocs
            sections["Core Python Reference"] = methoddocs
        else:
            # Plugin or regular package.
            sections["Python Reference"] = methoddocs

        toc_trees = []
        for caption, entries in sections.items():
            toc_tree = f".. toctree::\n   :caption: {caption}\n   :maxdepth: 1\n\n"
            for entry in entries:
                toc_tree += f"   {entry}\n"

            toc_trees.append(toc_tree)

        toc_tree_rst = "\n".join(toc_trees)
        restructured_text = f"{self._title_rst}\n\n{toc_tree_rst}"
        return self.parse_text_to_nodes(restructured_text)

    def _get_userguides(self) -> list[str]:
        guides = self._get_doc_entries(self.userguides_path)
        quickstart_name = "userguides/quickstart"
        if quickstart_name in guides:
            # Make sure quick start is first.
            guides = [quickstart_name, *[g for g in guides if g != quickstart_name]]

        return guides

    def _get_cli_references(self) -> list[str]:
        return self._get_doc_entries(self.commands_path)

    def _get_methoddocs(self) -> list[str]:
        return self._get_doc_entries(self.methoddocs_path)

    def _get_doc_entries(self, path: Path) -> list[str]:
        if not path.is_dir():
            return []

        return sorted(
            [f"{path.name}/{g.stem}" for g in path.iterdir() if g.suffix in (".md", ".rst")]
        )
