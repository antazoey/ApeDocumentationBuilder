from sphinx_ape.utils import extract_package_name


def test_extract_package_name_setup_py(temp_path):
    setup_py = temp_path / "setup.py"
    name = "ape-myplugin"
    content = f"""
#!/usr/bin/env python

from setuptools import find_packages, setup
extras_require = {{
    "test": [  # `test` GitHub Action jobs uses this
        "pytest>=6.0",  # Core testing package
    ],
}}
setup(
    name="{name}",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.12",
    ],
)
"""
    setup_py.write_text(content)

    actual = extract_package_name(temp_path)
    assert actual == name
