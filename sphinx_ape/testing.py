import subprocess
from pathlib import Path

from sphinx_ape._base import Documentation
from sphinx_ape.exceptions import ApeDocsBuildError, ApeDocsTestError


class DocumentationTester(Documentation):
    """
    Small wrapper around sphinx-build's doctest command.
    """

    @property
    def doctest_output_file(self) -> Path:
        """
        The path to doctest's output file.
        """
        return self.build_path.parent / "doctest" / "output.txt"

    def test(self):
        """
        Run the sphinx-build doctest command.

        Raises:
            :class:`~sphinx_ape.exceptions.ApeDocsTestError`
        """
        try:
            subprocess.run(
                ["sphinx-build", "-b", "doctest", "docs", "docs/_build/doctest"], check=True
            )
        except subprocess.CalledProcessError as err:
            raise ApeDocsBuildError(str(err)) from err

        if self.doctest_output_file.is_file():
            return

        output = self.doctest_output_file.read_text() if self.doctest_output_file.is_file() else ""
        if "0 failed" in output or "0 tests" in output:
            return

        raise ApeDocsTestError(output)
