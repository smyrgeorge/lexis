# Traducir

This repository contains documents and utilities for converting PDFs to Markdown. Below is a short guide to install
Docling and use it to convert a PDF (for example, the file under `workspace/estado-del-poder/estado-del-poder.pdf`) into
Markdown.

## Install Docling

Docling is a Python package. You can install it in a virtual environment.

- Requirements: Python 3.9+ and `pip`

Create and activate a virtual environment (recommended):

```shell
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install Docling:

```shell
pip install docling

# Also you may have to install some dependencies:
pip install opencv-python
```

## Convert a PDF to Markdown

You can use Docling via its command-line interface (CLI).

```shell
# Use one of the following commands to convert a PDF to Markdown:
docling workspace/estado-del-poder/estado-del-poder.pdf --to md --output out
docling workspace/estado-del-poder/estado-del-poder.pdf --to md --output out --image-export-mode placeholder
docling workspace/estado-del-poder/estado-del-poder.pdf --to md --output out --no-tables --image-export-mode placeholder
```

The resulting Markdown file will be written to `out/estado-del-poder.md`.

## Notes

- Large or scanned PDFs may require additional dependencies (e.g., OCR backends). Consult Docling's documentation for
  optional extras and platform-specific setup.
- For best results, ensure the input PDF has selectable text. If OCR is needed, check Docling's options or integrate an
  OCR engine.
- Refer to the Docling project README for the most up-to-date CLI flags and API names, as they may evolve.

