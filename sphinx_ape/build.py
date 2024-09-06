import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from sphinx_ape._base import Documentation
from sphinx_ape._utils import extract_source_url, git, replace_tree, sphinx_build
from sphinx_ape.exceptions import ApeDocsBuildError, ApeDocsPublishError

REDIRECT_HTML = """
<!DOCTYPE html>
<meta charset="utf-8">
<title>Redirecting...</title>
<meta http-equiv="refresh" content="0; URL=./{}/">
"""


class BuildMode(Enum):
    LATEST = 0
    """Build and then push to 'latest/'"""

    RELEASE = 1
    """Build and then push to 'stable/', 'latest/', and the version's release tag folder"""

    @classmethod
    def init(cls, identifier: Optional[Union[str, "BuildMode"]] = None) -> "BuildMode":
        if identifier is None:
            # Default.
            return BuildMode.LATEST

        elif isinstance(identifier, BuildMode):
            return identifier

        elif isinstance(identifier, int):
            return BuildMode(identifier)

        elif isinstance(identifier, str):
            if "." in identifier:
                # Click being weird, value like "buildmode.release".
                identifier = identifier.split(".")[-1].upper()

            # GitHub event name.
            return BuildMode.RELEASE if identifier.lower() == "release" else BuildMode.LATEST

        # Unexpected.
        raise TypeError(identifier)


class DocumentationBuilder(Documentation):
    """
    Builds either "latest", or "stable" / "release"
    documentation.
    """

    def __init__(
        self,
        mode: Optional[BuildMode] = None,
        base_path: Optional[Path] = None,
        name: Optional[str] = None,
        pages_branch_name: Optional[str] = None,
    ) -> None:
        self.mode = BuildMode.LATEST if mode is None else mode
        super().__init__(base_path, name)
        self._pages_branch_name = pages_branch_name or "gh-pages"

    def build(self):
        """
        Build the documentation.

        Example:
            >>> from sphinx_ape.build import BuildMode, DocumentationBuilder
            >>> from pathlib import Path
            >>> builder = DocumentationBuilder(
            ...   mode=BuildMode.LATEST,
            ...   base_path=Path("."),
            ...   name="sphinx-ape"
            ... )
            >>> builder.build()

        Raises:
            :class:`~sphinx_ape.exceptions.ApeDocsBuildError`: When
              building fails.
        """

        if self.mode is BuildMode.LATEST:
            # TRIGGER: Push to 'main' branch. Only builds latest.
            self._sphinx_build(self.latest_path)

        elif self.mode is BuildMode.RELEASE:
            # TRIGGER: Release on GitHub
            self._build_release()

        else:
            # Unknown 'mode'.
            raise ApeDocsBuildError(f"Unsupported build-mode: {self.mode}")

        self._setup_redirect()

    def publish(self, repository: Optional[str] = None, push: bool = True):
        """
        Publish the documentation to GitHub pages.
        Meant to be run in CI/CD on releases.

        Args:
            repository (Optional[str]]): The repository name. Defaults to GitHub env-var
              or extraction from setup file.
            push (bool): Set to ``False`` to skip git add, commit, and push.

        Raises:
            :class:`~sphinx_ape.exceptions.ApeDocsPublishError`: When
              publishing fails.
        """
        try:
            self._publish(repository=repository, push=push)
        except Exception as err:
            raise ApeDocsPublishError(str(err)) from err

    def _publish(self, repository: Optional[str] = None, push: bool = True):
        if repository:
            repo_url = f"https://github.com/{repository}"
        else:
            repo_url = extract_source_url()

        gh_pages_path = Path.cwd() / "gh-pages"
        git(
            "clone",
            repo_url,
            "--branch",
            self._pages_branch_name,
            "--single-branch",
            self._pages_branch_name,
        )
        try:
            # Any built docs get added; the docs that got built are based on
            # the mode parameter.
            for path in self.build_path.iterdir():
                if not path.is_dir() or path.name.startswith(".") or path.name == "doctest":
                    continue

                elif path.name == "index.html":
                    (gh_pages_path / "index.html").write_text(path.read_text())

                else:
                    shutil.copytree(path, gh_pages_path / path.name, dirs_exist_ok=True)

            no_jykell_file = gh_pages_path / ".nojekyll"
            no_jykell_file.touch(exist_ok=True)

            if push:
                here = os.getcwd()
                try:
                    os.chdir(str(gh_pages_path))
                    # NOTE: CI/CD does not push here but instead uses the
                    #  push-action w/ a login.
                    git("add", ".")
                    git("commit", "-m", "Update documentation", "-a")
                    git("push", "origin", "gh-pages")
                finally:
                    os.chdir(here)

        finally:
            if push:
                # Only delete if we are done pushing.
                # Else, leave so the GH action can push.
                shutil.rmtree(gh_pages_path, ignore_errors=True)

    def _build_release(self):
        if not (tag := git("describe", "--tag")):
            raise ApeDocsBuildError("Unable to find release tag.")

        if "beta" in tag or "alpha" in tag:
            # Avoid creating release directory for beta
            # or alpha releases. Only update "stable" and "latest".
            self._sphinx_build(self.stable_path)
            replace_tree(self.stable_path, self.latest_path)

        else:
            # Use the tag to create a new release folder.
            build_dir = self.build_path / tag
            self._sphinx_build(build_dir)

            if not build_dir.is_dir():
                return

            # Clean-up unnecessary extra 'fonts/' directories to save space.
            # There should still be one in 'latest/'
            for font_dirs in build_dir.glob("**/fonts"):
                if font_dirs.is_dir():
                    shutil.rmtree(font_dirs)

            # Replace 'stable' and 'latest' with this version.
            for path in (self.stable_path, self.latest_path):
                replace_tree(build_dir, path)

    def _setup_redirect(self):
        self.build_path.mkdir(exist_ok=True, parents=True)

        # In the case for local dev (or a new docs-site), the 'stable/'
        # path will not exist yet, so use 'latest/' instead.
        redirect = "stable" if self.stable_path.is_dir() else "latest"

        index_file = self.build_path / "index.html"
        index_file.unlink(missing_ok=True)
        index_file.write_text(REDIRECT_HTML.format(redirect))

    def _sphinx_build(self, dst_path):
        sphinx_build(dst_path, self.docs_path)
