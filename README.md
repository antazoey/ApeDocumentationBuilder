# Quick Start

A script that uses sphinx to develop documentation for ApeWorX plugins.

## Dependencies

- [python3](https://www.python.org/downloads) version 3.9 up to 3.12.

## Quick Usage

To use this to build the documentation in an Ape plugin, add this to your documentation workflow (e.g. your `.github/workflows/docs.yaml` file).

```bash
        - name: Clone ApeDocumentationBuilder
          run: git clone https://github.com/ApeWorX/ApeDocumentationBuilder.git

        - name: Set up environment variable
          run: echo "GITHUB_REPO=$(echo ${GITHUB_REPOSITORY} | cut -d'/' -f2)" >> $GITHUB_ENV

        - name: Build HTML artifact
          run: |
            cd ApeDocumentationBuilder
            python build_docs.py

```

## Development

Please see the [contributing guide](CONTRIBUTING.md) to learn more how to contribute to this project.
Comments, questions, criticisms and pull requests are welcomed.
