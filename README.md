# Lexis

![Alt text](docs/img/logo-wide.png)

A collection of utilities for translating large documents and books.

## About

Lexis is a powerful toolkit designed to streamline the process of translating lengthy documents, books, and PDFs using
modern Large Language Models (LLMs) like Claude and ChatGPT.

The project addresses the challenges of translating large
documents by providing utilities to split PDFs into manageable chunks, convert them to Markdown format, and perform
context-aware translations that maintain consistency across chunk boundaries. Whether you're working with a small
article or a multi-hundred-page book, Lexis provides the tools to automate and optimize the translation workflow while
preserving formatting and ensuring high-quality results.

## Setup

### Initialize Python Environment

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Install Requirements

```bash
pip install -r requirements.txt
```

### Configure API Keys

Create a `.env` and add your `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY` like so:

```properties
# API Keys for Translation Services
# Anthropic API Key (for Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OpenAI API Key (for ChatGPT)
OPENAI_API_KEY=your_openai_api_key_here

```

## Usage

To translate a large PDF document, you'll typically follow a three-step process:

1. **[Split the PDF](#1-split-a-pdf-file-into-chunks)** (optional, for large files) - Break large PDFs into smaller
   chunks
2. **[Convert to Markdown](#2-convert-pdfs-to-markdown)** - Transform PDF files into editable Markdown format
3. **[Translate](#3-translate-markdown-files)** - Use LLMs to translate the Markdown files to your target language

Each step is detailed below.

#### 1. Split a PDF File into Chunks

Split a large PDF into smaller chunks:

```bash
python scripts/chunk_pdf.py input.pdf -p 10 -o output_directory
```

#### 2. Convert PDFs to Markdown

Process all PDFs in a directory.

```bash
# Basic usage
python scripts/pdf_to_md.py <directory_path>

# Custom line width
python scripts/pdf_to_md.py <directory_path> --line-width 100

# Disable line wrapping
python scripts/pdf_to_md.py <directory_path> --no-wrap
```

Markdown files will be placed in the same directory as the source PDFs.

#### 3. Translate Markdown Files

Translate markdown files using LLMs (Claude or ChatGPT). Supports both single files and batch processing of directories.
Translated files are placed in the same directory as the source file by default.

**Key Features:**

- **Context-aware translation**: Automatically includes lines from previous/next chunks to improve translation quality
  across chunk boundaries
- **Smart filtering**: Skips already translated files when processing directories
- **Custom dictionaries**: Support for specialized terminology

```bash
# Translate a single file with Claude (default)
python scripts/translate_md.py input.md -s Spanish -t English

# Translate all .md files in a directory (with context from adjacent chunks)
python scripts/translate_md.py ./markdown-dir -s Spanish -t English

# Customize context lines (default is 5, set to 0 to disable)
python scripts/translate_md.py ./markdown-dir -s Spanish -t English -c 10

# Using OpenAI
python scripts/translate_md.py input.md -p openai -s Spanish -t English

# With custom dictionary
python scripts/translate_md.py input.md -s es -t en -d dictionary.csv

# With custom output directory
python scripts/translate_md.py input.md -s Spanish -t English -o ./translations

# With custom prompt and model
python scripts/translate_md.py input.md -s Spanish -t English --prompt "Your custom prompt here" -m gpt-4o-mini
```

**Dictionary format** (`dictionary.csv`):

```csv
source,target
término1,term1
término2,term2
```

### Quick Workflow Examples

**Manual Steps - Small PDF Translation:**

```bash
python scripts/pdf_to_md.py ./document.pdf
python scripts/translate_md.py ./document.md -s Spanish -t English
```

**Manual Steps - Large PDF Translation:**

```bash
python scripts/chunk_pdf.py large-book.pdf -p 10 -o ./chunks
python scripts/pdf_to_md.py ./chunks
python scripts/translate_md.py ./chunks -s Spanish -t English
```

See [docs/README.md](docs/README.md) for complete workflows and advanced usage.
