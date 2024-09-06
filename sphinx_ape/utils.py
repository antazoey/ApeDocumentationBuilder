import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Union

import tomli

from sphinx_ape.exceptions import ApeDocsBuildError

# Avoid needing to have common Ape packages re-configure this.
PACKAGE_ALIASES = {
    "eth-ape": "ape",
}


def git(*args):
    return subprocess.check_output(["git", *args]).decode("ascii").strip()


def new_dir(path: Path) -> Path:
    if path.is_dir():
        shutil.rmtree(path)

    path.mkdir(parents=True)
    return path


def sphinx_build(dst_path: Path, source_dir: Union[Path, str]) -> Path:
    path = new_dir(dst_path)
    try:
        subprocess.check_call(["sphinx-build", str(source_dir), str(path)])
    except subprocess.SubprocessError as err:
        raise ApeDocsBuildError(f"Command 'sphinx-build docs {path}' failed.") from err

    return path


def _extract_name_from_setup_py(file_path: Path) -> Optional[str]:
    content = file_path.read_text()
    if match := re.search(r"name\s*=\s*['\"](.+?)['\"]", content):
        return match.group(1)

    return None


def _extract_name_from_pyproject_toml(file_path: Path) -> Optional[str]:
    """Extract package name from pyproject.toml."""
    with open(file_path, "rb") as file:
        pyproject = tomli.load(file)

    if "tool" in pyproject and "poetry" in pyproject["tool"]:
        return pyproject["tool"]["poetry"].get("name")

    elif "project" in pyproject:
        return pyproject["project"].get("name")

    return None


def get_package_name() -> str:
    if env_var := os.getenv("GITHUB_REPO"):
        return env_var

    # Figure it out.
    return extract_package_name()


def extract_package_name(directory: Optional[Path] = None) -> str:
    """Detect and extract the package name from the project files."""
    directory = directory or Path.cwd()
    pkg_name = None
    if (directory / "setup.py").is_file():
        pkg_name = _extract_name_from_setup_py(directory / "setup.py")
    if pkg_name is None and (directory / "pyproject.toml").is_file():
        pkg_name = _extract_name_from_pyproject_toml(directory / "pyproject.toml")
    if pkg_name is None:
        raise ApeDocsBuildError("No package name found.")

    return PACKAGE_ALIASES.get(pkg_name, pkg_name)


def replace_tree(base_path: Path, dst_path: Path):
    shutil.rmtree(dst_path, ignore_errors=True)
    shutil.copytree(base_path, dst_path)
