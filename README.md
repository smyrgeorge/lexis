# Lexis

![Alt text](docs/img/logo-wide.png)

A collection of utilities for translating large documents and books.

## About

Lexis is a powerful toolkit designed to streamline the process of translating lengthy documents, books, and PDFs using
modern Large Language Models (LLMs).

The project addresses the challenges of translating large
documents by providing utilities to split PDFs into manageable chunks, convert them to Markdown format, and perform
context-aware translations that maintain consistency across chunk boundaries. Whether you're working with a small
article or a multi-hundred-page book, Lexis provides the tools to automate and optimize the translation workflow while
preserving formatting and ensuring high-quality results.

> [!NOTE]
> This project does not attempt to replace the complete process of translating a book or large document. Instead, it aims
> to minimize the effort required to generate a high-quality first draft translation, allowing translators to focus their
> time and expertise on refining the translation rather than performing the initial, time-consuming conversion work.

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

Create a `.env` and add your `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY`, `LIBRETRANSLATE_API_KEY` like so:

```properties
# API Keys for Translation Services
# Anthropic API Key (for Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OpenAI API Key (for ChatGPT)
OPENAI_API_KEY=your_openai_api_key_here
# LibreTranslate API KEY (for LibreTranslate)
LIBRETRANSLATE_API_KEY=your_libretranslate_api_key_here
```

## Usage

To translate a large PDF document, you'll typically follow a three-step process:

1. **[Split the PDF](#1-split-a-pdf-file-into-chunks)** (optional, for large files)—Break large PDFs into smaller
   chunks
2. **[Convert to Markdown](#2-convert-pdfs-to-markdown)**—Transform PDF files into editable Markdown format
3. **[Translate](#3-translate-markdown-files)**—Use LLMs to translate the Markdown files to your target language

Each step is detailed below.

#### 1. Split a PDF File into Chunks

For large documents, splitting into smaller chunks is recommended because the conversion and translation tools work
better with smaller document sizes (1–5 pages). This ensures higher quality output and more reliable processing.

Split a large PDF into smaller chunks:

```bash
python scripts/chunk_pdf.py input.pdf -p 10 -o output_directory
```

The `-p` parameter specifies how many pages per chunk (e.g., `-p 10` creates chunks of 10 pages each).

For more options, see the source code: [scripts/chunk_pdf.py](scripts/chunk_pdf.py)

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

For more options, see the source code: [scripts/pdf_to_md.py](scripts/pdf_to_md.py)

#### 3. Translate Markdown Files

Translate markdown files using LLMs (Claude or ChatGPT) or LibreTranslate. Supports both single files and batch processing of directories.
Translated files are placed in the same directory as the source file by default.

**Key Features:**

- **Context-aware translation** (LLM providers only): Automatically includes lines from previous/next chunks to improve translation quality
  across chunk boundaries
- **Smart filtering**: Skips already translated files when processing directories
- **Custom dictionaries** (LLM providers only): Add custom words or phrases that should be translated in a specific way. The dictionary is
  appended to the translator's context to ensure consistent terminology throughout your document
- **Multiple providers**: Choose between Claude (Anthropic), ChatGPT (OpenAI), or LibreTranslate (free, open-source)

For more options, see the source code: [scripts/translate_md.py](scripts/translate_md.py)

##### Translation Engines

**1. Claude (Anthropic) - Default**
- Requires: `ANTHROPIC_API_KEY` in `.env` file
- Best for: High-quality translations with context awareness
- Supports: Custom dictionaries, context from adjacent chunks, custom prompts, style guidance via `--style`

```bash
# Basic usage (Claude is the default provider)
python scripts/translate_md.py input.md -s Spanish -t English

# With custom model
python scripts/translate_md.py input.md -s Spanish -t English -m claude-sonnet-4-5-20250929
```

**2. ChatGPT (OpenAI)**
- Requires: `OPENAI_API_KEY` in `.env` file
- Best for: Fast, reliable translations with GPT models
- Supports: Custom dictionaries, context from adjacent chunks, custom prompts, style guidance via `--style`

```bash
# Using OpenAI
python scripts/translate_md.py input.md -p openai -s Spanish -t English

# With custom model
python scripts/translate_md.py input.md -p openai -s Spanish -t English -m gpt-5
```

**3. LibreTranslate (Free, Open-Source)**
- Requires: No API key (optional: `LIBRETRANSLATE_API_KEY` for rate limit increase)
- Best for: Free translations without API costs, self-hosted deployments
- Requires language codes (e.g., 'es', 'en')
- Note: Does not support custom dictionaries or context from adjacent chunks

```bash
# Using LibreTranslate (free, public API)
python scripts/translate_md.py input.md -p libretranslate -s es -t en

# Using self-hosted LibreTranslate server
python scripts/translate_md.py input.md -p libretranslate -s es -t en --libretranslate-url http://localhost:5000

# With API key (optional, for higher rate limits)
# Add LIBRETRANSLATE_API_KEY to your .env file
python scripts/translate_md.py input.md -p libretranslate -s es -t en
```


**Dictionary format** (`dictionary.txt`):

Use a TXT file to define how specific terms should be translated. This is useful for technical terms, proper nouns, or
specialized vocabulary that should be consistently translated in a specific way. You can provide multiple translation
hints per term, separated by commas.

```
# Dictionary format: term: translation 1, translation 2, ...
término técnico: technical term
nombre propio: Proper Name
frase especial: special phrase, unique expression
```

### Quick Workflow Examples

**Manual Steps—Small PDF Translation:**

```bash
python scripts/pdf_to_md.py ./document.pdf
python scripts/translate_md.py ./document.md -s Spanish -t English
```

**Manual Steps—Large PDF Translation:**

```bash
python scripts/chunk_pdf.py large-book.pdf -p 10 -o ./chunks
python scripts/pdf_to_md.py ./chunks
python scripts/translate_md.py ./chunks -s Spanish -t English
```
