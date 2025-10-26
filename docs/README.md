# Lexis Documentation

Complete documentation for all Lexis scripts and workflows.

## Overview

Lexis is a comprehensive toolkit for converting, chunking, and translating large documents. It provides a complete
pipeline from PDF to translated text with intelligent chunking and context-aware translation.

## Quick Links

- [batch_convert_pdf_to_md.md](pdf_to_md.md) - Efficiently convert multiple PDFs to Markdown
- [chunk_pdf.md](chunk_pdf.md) - Split large PDFs into manageable chunks
- [chunk_md.md](chunk_md.md) - Intelligently split markdown files
- [translate_md.md](translate_md.md) - Translate markdown with context awareness
- [docling.md](docling.md) - Docling installation and usage guide

## Scripts Overview

### PDF Processing

#### [batch_convert_pdf_to_md.py](pdf_to_md.md)

Batch converts PDF files to Markdown using docling's Python API.

**Key Feature**: Loads docling models once for all files (much faster than CLI approach)

```bash
python scripts/pdf_to_md.py ./pdfs
```

#### [chunk_pdf.py](chunk_pdf.md)

Splits PDF files into smaller chunks by page count.

**Best for**: Large PDFs that need to be processed in pieces

```bash
python scripts/chunk_pdf.py large-document.pdf -p 10
```

### Markdown Processing

#### [chunk_md.py](chunk_md.md)

Intelligently chunks markdown files by headings, characters, or tokens.

**Best for**: Splitting documents by logical structure or size constraints

```bash
# By headings (chapters, sections)
python scripts/chunk_md.py document.md --heading-level 1

# By token count (for LLM limits)
python scripts/chunk_md.py document.md --mode tokens --max-tokens 2000
```

### Translation

#### [translate_md.py](translate_md.md)

Advanced markdown translation using Claude or ChatGPT with context awareness.

**Key Features**:

- Context from adjacent chunks for better translation quality
- Automatic detection of already-translated files
- Custom terminology dictionaries
- Batch directory processing

```bash
# Translate directory with context
python scripts/translate_md.py ./chunks -s Spanish -t English

# With custom dictionary
python scripts/translate_md.py ./chunks -s Spanish -t English -d dictionary.csv
```

## Common Workflows

### Workflow 1: PDF to Translated Text (Small Files)

For PDFs under ~50 pages:

```bash
# 1. Convert PDF to Markdown
python scripts/pdf_to_md.py ./document.pdf

# 2. Translate
python scripts/translate_md.py ./document.md -s Spanish -t English
```

### Workflow 2: Large PDF Translation (Recommended)

For large PDFs, split first for better results:

```bash
# 1. Split PDF into chunks
python scripts/chunk_pdf.py large-book.pdf -p 10 -o ./chunks

# 2. Convert chunks to Markdown
python scripts/pdf_to_md.py ./chunks

# 3. Translate with context
python scripts/translate_md.py ./chunks -s Spanish -t English
```

**Why This Works Better**:

- Smaller chunks = faster processing
- Context awareness maintains coherence across chunks
- Can resume if interrupted
- Parallel processing possible

### Workflow 3: Structured Document Translation

For documents with clear structure (books, manuals):

```bash
# 1. Convert to Markdown
python scripts/pdf_to_md.py ./book.pdf

# 2. Split by chapter headings
python scripts/chunk_md.py ./book.md --heading-level 1 -o ./chapters

# 3. Translate chapters with dictionary
python scripts/translate_md.py ./chapters -s Spanish -t English -d ./terms.csv
```

### Workflow 4: LLM Context Window Optimization

For processing with token limits:

```bash
# 1. Convert to Markdown
python scripts/pdf_to_md.py ./document.pdf

# 2. Chunk by token count (e.g., 2000 tokens for 8K models)
python scripts/chunk_md.py ./document.md --mode tokens --max-tokens 2000

# 3. Translate (context lines won't exceed limits)
python scripts/translate_md.py ./document_chunks -s Spanish -t English -c 3
```

## Feature Comparison

| Feature                | chunk_pdf.py | chunk_md.py           | translate_md.py     |
|------------------------|--------------|-----------------------|---------------------|
| **Input**              | PDF          | Markdown              | Markdown            |
| **Output**             | PDF chunks   | Markdown chunks       | Translated markdown |
| **Splitting Strategy** | Page count   | Headings/chars/tokens | N/A                 |
| **Context Awareness**  | No           | No                    | Yes                 |
| **Batch Processing**   | No           | No                    | Yes                 |
| **Custom Dictionary**  | No           | No                    | Yes                 |
| **LLM Integration**    | No           | No                    | Yes                 |

## Installation

### Basic Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### API Keys (for Translation)

Create `.env` file:

```bash
# For Claude
ANTHROPIC_API_KEY=your_key_here

# For ChatGPT
OPENAI_API_KEY=your_key_here
```

See [translate_md.md](translate_md.md) for detailed setup.

## Best Practices

### Chunking

1. **PDF Chunking**: 10-20 pages per chunk is optimal
2. **Markdown by Headings**: Best for structured documents
3. **Markdown by Tokens**: Essential when working with LLM APIs
4. **Overlap**: Use 10-20% overlap for translation tasks

### Translation

1. **Context Lines**: 5 lines (default) balances quality and cost
2. **Dictionaries**: Pre-define technical terms for consistency
3. **Batch Processing**: Process directories, not individual files
4. **Model Selection**:
    - `claude-sonnet-4-5`: Best quality (literary, technical)
    - `gpt-4o`: Fast, cost-effective
    - `gpt-4o-mini`: Drafts and testing

### Performance

1. **Use Python batch converter**: 3-5x faster than bash version
2. **Split large files first**: Better for memory and resumability
3. **Process chunks in parallel**: Use multiple terminals for speed
4. **Monitor costs**: Track API usage with smaller test runs first

## Troubleshooting

### Common Issues

**"docling not found"**

```bash
pip install docling opencv-python
```

**"API key not found"**

```bash
# Create .env file with your keys
cp .env.example .env
# Edit .env and add your API keys
```

**"Out of tokens/context"**

```bash
# Reduce chunk size or context lines
python scripts/chunk_md.py doc.md --mode tokens --max-tokens 1500
python scripts/translate_md.py ./chunks -s es -t en -c 3
```

**"Translation quality poor at chunk boundaries"**

```bash
# Increase context lines
python scripts/translate_md.py ./chunks -s Spanish -t English -c 10
```

## Advanced Topics

### Custom Prompts

Override translation behavior:

```bash
python scripts/translate_md.py doc.md \
  -s Spanish -t English \
  --prompt "Translate professionally from {source} to {target}. Use academic tone."
```

### Parallel Processing

Process multiple chunks simultaneously:

```bash
# Terminal 1
python scripts/translate_md.py ./chunks/batch1 -s es -t en

# Terminal 2
python scripts/translate_md.py ./chunks/batch2 -s es -t en
```

### Resume Interrupted Translations

The script automatically skips already-translated files:

```bash
# Run again after interruption - already completed files are skipped
python scripts/translate_md.py ./chunks -s Spanish -t English
```

## Support

- **Issues**: Report at [GitHub Issues](https://github.com/anthropics/claude-code/issues)
- **Documentation**: This docs folder
- **Examples**: See individual script documentation

## Contributing

When adding new scripts:

1. Add comprehensive docstrings
2. Include usage examples in the script header
3. Create corresponding documentation in `docs/`
4. Update this README with the new script
5. Add to relevant workflows section

## License

See project LICENSE file.
