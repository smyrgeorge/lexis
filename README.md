# Traducir

A collection of utilities for translating large documents.

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

Edit `.env` and add your `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY`

## Usage

### Split PDF into Chunks

Split a large PDF into smaller chunks:

```bash
python scripts/chunk_pdf.py input.pdf -p 10 -o output_directory
```

### Batch Convert PDFs to Markdown

Process all PDFs in a directory. The Python version is recommended as it loads docling models only once, making it much faster for multiple files.

**Python version (recommended):**
```bash
# Basic usage
python scripts/batch_convert_pdf_to_md.py <directory_path>

# Custom line width
python scripts/batch_convert_pdf_to_md.py <directory_path> --line-width 100

# Disable line wrapping
python scripts/batch_convert_pdf_to_md.py <directory_path> --no-wrap
```

**Bash version:**
```bash
./scripts/batch_convert_pdf_to_md.sh <directory_path>
```

Markdown files will be placed in the same directory as the source PDFs.

### Translate Markdown Files

Translate markdown files using LLMs (Claude or ChatGPT). Supports both single files and batch processing of directories. Translated files are placed in the same directory as the source file by default.

**Key Features:**
- **Context-aware translation**: Automatically includes lines from previous/next chunks to improve translation quality across chunk boundaries
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

## Documentation

See [docs](docs) for more details.
