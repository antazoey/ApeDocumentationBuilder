import os
import sys
from pathlib import Path

from sphinx.util import logging
from sphinx.application import Sphinx

from sphinx_ape.sphinx_ext.directives import DynamicTocTree
from sphinx_ape.utils import get_package_name


logger = logging.getLogger(__name__)


def ensure_quickstart_exists(app, cfg):
    """
    This will generate the quickstart guide if needbe.
    I recommend committing the files it generates.
    """
    
    userguides_path = Path(app.srcdir) / "userguides"
    quickstart_path = userguides_path / "quickstart.md"
    if quickstart_path.is_file():
        # Already exists.
        return
    
    logger.info("Generating userguides/quickstart.md")
    userguides_path.mkdir(exist_ok=True)
    quickstart_path.write_text("```{include} ../../README.md\n```\n")


def setup(app: Sphinx):
    """Set default values for various Sphinx configurations."""

    # For building and serving multiple projects at once,
    # we situate ourselves in the parent directory.
    sys.path.insert(0, os.path.abspath(".."))

    # Register the hook that generates the quickstart file if needbe.
    app.connect("config-inited", ensure_quickstart_exists)

    # Configure project and other one-off items.
    package_name = get_package_name()
    app.config.project = package_name
    app.config.copyright = "2024, ApeWorX LTD"
    app.config.author = "ApeWorX Team"

    app.config.exclude_patterns = list(
        set(app.config.exclude_patterns).union({"_build", ".DS_Store"})
    )
    app.config.source_suffix = [".rst", ".md"]
    app.config.master_doc = "index"

    # Automatically add required extensions.
    default_extensions = {
        "myst_parser",
        "sphinx_click",
        "sphinx.ext.autodoc",
        "sphinx.ext.autosummary",
        "sphinx.ext.doctest",
        "sphinx.ext.napoleon",
        "sphinx_rtd_theme",
        "sphinx_plausible",
    }

    # Ensure these have been loaded before continuing.
    for ext in default_extensions:
        app.setup_extension(ext)

    app.config.extensions = list(set(app.config.extensions).union(default_extensions))

    # Plausible config.
    if not getattr(app.config, "plausible_domain", None):
        app.config.plausible_domain = "docs.apeworx.io"

    # Configure the HTML workings.
    static_dir = Path(__file__).parent.parent.parent / "_static"
    app.config.html_theme = "shibuya"
    app.config.html_favicon = str(static_dir / "favicon.ico")
    app.config.html_baseurl = package_name
    app.config.html_static_path = [str(static_dir)]
    app.config.html_theme_options = {
        "light_logo": "_static/logo_grey.svg",
        "dark_logo": "_static/logo_green.svg",
        "accent_color": "lime",
    }

    # All MyST config.
    app.config.myst_all_links_external = True

    # Any config starting with "auto".
    app.config.autosummary_generate = True
    exclude_members = (
        # Object.
        "__weakref__",
        "__metaclass__",
        "__init__",
        "__format__",
        "__new__",
        "__dir__",
        # Pydantic.
        "model_config",
        "model_fields",
        "model_post_init",
        "model_computed_fields",
        # EthPydanticTypes.
        "__ape_extra_attributes__",
    )
    app.config.autodoc_default_options = {"exclude-members": ", ".join(exclude_members)}

    # Add the directive enabling the dynamic-TOC.
    app.add_directive("dynamic-toc-tree", DynamicTocTree)

    # Output data needed for the rest of the build.
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
