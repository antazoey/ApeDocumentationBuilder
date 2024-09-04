"""
This script is meant for building the documentation in both
core Ape as well as any Ape plugin. This script may also work
for regular Python packages with a documentation-strategy
similar to Ape.

Along with this script is a custom GitHub action.
There are three GitHub events that trigger this script:

1. Push to 'main': we build into 'latest/'.
    The GitHub action will commit these changes to the 'gh-pages' branch.

2. Release: we copy 'latest/' into the release dir, as well as to 'stable/'.
    The GitHub action will commit these changes to the 'gh-pages' branch.

3. Pull requests or local development: We ensure a successful build.
"""

import subprocess
from pathlib import Path

import click

from sphinx_ape.build import BuildMode, DocumentationBuilder
from sphinx_ape.exceptions import ApeDocsBuildError
from sphinx_ape.utils import get_package_name


@click.group()
def cli():
    """
    Documentation CLI
    """


def build_mode_option():
    return click.option(
        "--mode",
        callback=lambda c, p, v: BuildMode.init(v),
        type=BuildMode,
        default=BuildMode.LATEST,
    )


def package_name_option():
    return click.option(
        "--name",
        "package_name",
        callback=lambda c, p, v: v or get_package_name(),
    )


@cli.command()
@click.argument("base_path", type=Path)
@build_mode_option()
@package_name_option()
def build(base_path, mode, package_name):
    """
    Build an Ape python package's documentation
    """
    click.echo(f"Building '{package_name}' '{mode.name}'.")
    builder = DocumentationBuilder(mode, base_path=base_path, name=package_name)

    try:
        builder.build()
    except ApeDocsBuildError as err:
        click.echo(f"ERROR: {err}", err=True)


@cli.command()
@click.argument("base_path", type=Path)
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=1337)
@click.option("--open", is_flag=True, help="Open page in browser")
def serve(base_path, host, port, open):
    """
    Start a web-server to view the documentation
    """
    build_path = base_path / "docs" / "_build"
    try:
        process = subprocess.Popen(
            [
                "python",
                "-m",
                "http.server",
                "--directory",
                str(build_path),
                "--bind",
                host,
                f"{port}",
            ],
            universal_newlines=True,
        )
        if open:
            url = f"http://{host}:{port}/"
            built_docs = [
                b.name for b in build_path.iterdir() if b.is_dir() and not b.name.startswith(".")
            ]
            if len(built_docs) == 1:
                # Only one package, dir-listing not necessary.
                url = f"{url}{built_docs[0]}/latest"

            click.launch(url)

        process.wait()

    except KeyboardInterrupt:
        click.echo("Server interrupted by user.")

    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)
