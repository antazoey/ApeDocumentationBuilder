from pathlib import Path

import pytest

from sphinx_ape.build import REDIRECT_HTML, BuildMode, DocumentationBuilder


class TestBuildMode:
    @pytest.mark.parametrize("val", ("latest", 0, "pull_request", "buildmode.latest"))
    def test_init_latest(self, val):
        mode = BuildMode.init("val")
        assert mode is BuildMode.LATEST

    @pytest.mark.parametrize("val", ("release", 1, "buildmode.release"))
    def test_init_release(self, val):
        mode = BuildMode.init(val)
        assert mode is BuildMode.RELEASE


class TestDocumentationBuilder:
    @pytest.fixture(autouse=True)
    def mock_sphinx(self, mocker):
        def run_mock_sphinx(path, *args, **kwargs):
            path.mkdir(parents=True)
            buildfile = path / "build.txt"
            buildfile.touch()

        mock = mocker.patch("sphinx_ape.build.sphinx_build")
        mock.side_effect = run_mock_sphinx
        return mock

    @pytest.fixture(autouse=True)
    def mock_git(self, mocker):
        return mocker.patch("sphinx_ape.build.git")

    def test_build_latest(self, mock_sphinx, temp_path):
        builder = DocumentationBuilder(mode=BuildMode.LATEST, base_path=temp_path)
        builder.build()
        call_path = mock_sphinx.call_args[0][0]
        self.assert_build_path(call_path, "latest")
        # Ensure re-direct exists and points to latest/.
        assert builder.index_file.is_file()
        expected_content = REDIRECT_HTML.format("latest")
        assert builder.index_file.read_text() == expected_content

    def test_build_release(self, mock_sphinx, mock_git, temp_path):
        tag = "v1.0.0"
        mock_git.return_value = tag
        builder = DocumentationBuilder(mode=BuildMode.RELEASE, base_path=temp_path)
        builder.build()
        call_path = mock_sphinx.call_args[0][0]
        self.assert_build_path(call_path, tag)
        # Latest and Stable should also have been created!
        self.assert_build_path(call_path.parent / "latest", "latest")
        self.assert_build_path(call_path.parent / "stable", "stable")

    @pytest.mark.parametrize("sub_tag", ("alpha", "beta"))
    def test_build_alpha_release(self, sub_tag, mock_sphinx, mock_git, temp_path):
        """
        We don't build version releases when using alpha or beta, but we
        still update "stable" and "latest".
        """
        tag = f"v1.0.0{sub_tag}"
        mock_git.return_value = tag
        builder = DocumentationBuilder(mode=BuildMode.RELEASE, base_path=temp_path)
        builder.build()
        call_path = mock_sphinx.call_args[0][0]
        self.assert_build_path(call_path, "stable")
        # Latest should also have been created!
        self.assert_build_path(call_path.parent / "latest", "latest")

    def assert_build_path(self, path: Path, expected: str):
        assert path.name == expected  # Tag, latest, or stable
        assert path.parent.name == "sphinx-ape"  # Project name, happens to be this lib
        assert path.parent.parent.name == "_build"  # Sphinx-ism
        assert path.parent.parent.parent.name == "docs"  # Sphinx-ism
