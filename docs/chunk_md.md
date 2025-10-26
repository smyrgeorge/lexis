# chunk_md.py

Intelligently splits large markdown files into smaller, manageable chunks using multiple strategies.

## Overview

This script provides flexible chunking strategies for markdown files, making large documents easier to process,
translate, or analyze. Unlike simple line-based splitting, it understands markdown structure and can split by semantic
boundaries.

## Key Features

- **Multiple Chunking Modes**:
    - **Heading**: Split by document structure (chapters, sections)
    - **Characters**: Split by character count with paragraph-aware breaks
    - **Tokens**: Split by approximate token count (useful for LLM context limits)

- **Smart Boundaries**: Tries to break at paragraph boundaries, not mid-sentence
- **Overlap Support**: For character/token modes, add overlap between chunks for context continuity
- **Descriptive Naming**: Heading mode uses actual heading text in filenames
- **Preserved Structure**: Maintains markdown formatting in all chunks

## Usage

### By Heading (Default)

```bash
# Split on # and ## headings
python scripts/chunk_md.py document.md

# Split only on # (top-level headings)
python scripts/chunk_md.py document.md --heading-level 1

# Split on #, ##, and ### headings
python scripts/chunk_md.py document.md --heading-level 3
```

### By Character Count

```bash
# ~5000 characters per chunk (default)
python scripts/chunk_md.py document.md --mode chars

# Custom character limit
python scripts/chunk_md.py document.md --mode chars --max-chars 3000

# With custom overlap
python scripts/chunk_md.py document.md --mode chars --max-chars 5000 --overlap 500
```

### By Token Count

```bash
# ~1000 tokens per chunk (default, ≈ 4000 chars)
python scripts/chunk_md.py document.md --mode tokens

# Custom token limit (good for LLM context windows)
python scripts/chunk_md.py document.md --mode tokens --max-tokens 2000
```

### Custom Output Directory

```bash
python scripts/chunk_md.py document.md -o ./my-chunks
```

## Command-Line Options

| Option            | Short | Description                                 | Default                |
|-------------------|-------|---------------------------------------------|------------------------|
| `input_file`      | -     | Input markdown file                         | Required               |
| `--output`        | `-o`  | Output directory                            | `<input_file>_chunks/` |
| `--mode`          | `-m`  | Chunking mode: `heading`, `chars`, `tokens` | `heading`              |
| `--heading-level` | -     | Max heading level to split on (1-6)         | 2                      |
| `--max-chars`     | -     | Max characters per chunk (chars mode)       | 5000                   |
| `--max-tokens`    | -     | Max tokens per chunk (tokens mode)          | 1000                   |
| `--overlap`       | -     | Overlap size for size-based chunking        | 200                    |

## Chunking Modes Explained

### 1. Heading Mode (Default)

Splits document by markdown headings (`#`, `##`, etc.).

**Best for**:

- Documents with clear structure (books, articles)
- When you want logical, semantic divisions
- Preserving document hierarchy

**Example**:

```markdown
# Chapter 1: Introduction

Content here...

## Section 1.1

More content...

# Chapter 2: Methods

Next chapter...
```

With `--heading-level 1`, creates 2 chunks (one per chapter).
With `--heading-level 2` (default), creates 3 chunks (by chapters and sections).

**Output Filenames**:

- `001-Chapter-1-Introduction.md`
- `002-Section-1-1.md`
- `003-Chapter-2-Methods.md`

### 2. Character Mode

Splits by character count, trying to break at paragraph boundaries.

**Best for**:

- Documents without clear heading structure
- Ensuring consistent chunk sizes
- Memory-constrained processing

**Features**:

- Looks for paragraph breaks (`\n\n`) near chunk boundaries
- Supports overlap for context continuity
- Falls back to hard break if no paragraph boundary found

**Example**:

```bash
python scripts/chunk_md.py document.md --mode chars --max-chars 5000 --overlap 200
```

Creates chunks of ~5000 characters with 200 character overlap.

### 3. Token Mode

Splits by approximate token count (1 token ≈ 4 characters).

**Best for**:

- Preparing text for LLM processing
- Respecting API token limits
- Consistent processing costs

**Token Approximation**:

- GPT models: ~1 token per 4 characters (English)
- Conservative estimate for reliable chunking

**Example**:

```bash
# For 8K context window models, use ~2000 tokens per chunk
python scripts/chunk_md.py document.md --mode tokens --max-tokens 2000
```

## Output Format

### Heading Mode

```
001-Introduction.md
002-Background.md
003-Methodology.md
...
```

### Character/Token Mode

```
001-chunk.md
002-chunk.md
003-chunk.md
...
```

## Use Cases

### 1. Book Translation Pipeline

```bash
# Convert PDF to markdown
python scripts/pdf_to_md.py ./book.pdf

# Chunk by chapters (level 1 headings)
python scripts/chunk_md.py ./book.md --heading-level 1 -o ./chapters

# Translate each chapter
python scripts/translate_md.py ./chapters -s Spanish -t English
```

### 2. LLM Processing

```bash
# Chunk for GPT-4 (8K context, use ~2K per chunk for safety)
python scripts/chunk_md.py large-doc.md --mode tokens --max-tokens 2000

# Process with overlap for context continuity
python scripts/chunk_md.py large-doc.md --mode tokens --max-tokens 2000 --overlap 500
```

### 3. Parallel Analysis

```bash
# Split into equal-sized chunks for parallel processing
python scripts/chunk_md.py document.md --mode chars --max-chars 10000
```

## Overlap Behavior

When using character or token modes with overlap:

```
Chunk 1: [-------- content --------]
                              [overlap]
Chunk 2:                  [overlap][-------- content --------]
                                                        [overlap]
Chunk 3:                                            [overlap][-------- content --------]
```

This ensures context continuity across chunk boundaries.

## Requirements

- Python 3.9+
- No external dependencies (uses only standard library)

## Example Output

### Heading Mode

```
Split into 5 chunks by heading level 2

Created: document_chunks/001-Introduction.md
Created: document_chunks/002-Background.md
Created: document_chunks/003-Methodology.md
Created: document_chunks/004-Results.md
Created: document_chunks/005-Conclusion.md

All chunks saved to: document_chunks
```

### Character Mode

```
Split into 12 chunks by character count (~5000 chars each)

Created: document_chunks/001-chunk.md
Created: document_chunks/002-chunk.md
...
Created: document_chunks/012-chunk.md

All chunks saved to: document_chunks
```

## Error Handling

- Validates input file exists
- Press `Ctrl+C` to gracefully cancel

## Tips

- **Heading Mode**: Best for structured documents; requires proper markdown heading usage
- **Character Mode**: Good for consistent sizes; use overlap for better context
- **Token Mode**: Essential for LLM APIs with token limits
- **Overlap**: 10-20% overlap is good for translation tasks

## See Also

- [chunk_pdf.md](chunk_pdf.md) - Alternative: chunk before conversion
- [translate_md.md](translate_md.md) - Translate chunked markdown files
- [batch_convert_pdf_to_md.md](pdf_to_md.md) - Convert PDFs to markdown first
