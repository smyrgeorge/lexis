# batch_convert_pdf_to_md.py

Efficiently batch converts multiple PDF files to Markdown format using docling's Python API.

## Overview

This script processes all PDF files in a directory and converts them to Markdown. Unlike command-line alternatives that
load docling models for each file, this script loads the models **once** and reuses them for all conversions, making it
significantly faster for processing multiple PDFs.

## Key Features

- **Efficient Model Loading**: Docling models are loaded once at startup and reused for all PDFs
- **Automatic Line Wrapping**: Wraps markdown lines to a configurable width (default: 120 characters)
- **Smart Wrapping Logic**: Preserves markdown structure (doesn't wrap headers, code blocks, or tables)
- **Same-Directory Output**: Converted markdown files are saved alongside their source PDFs
- **Progress Tracking**: Shows clear progress and error messages for each file
- **Graceful Error Handling**: Continues processing remaining files even if one fails

## Usage

### Basic Usage

```bash
python scripts/pdf_to_md.py <directory_path>
```

This will:

- Process all `.pdf` files in the specified directory
- Save `.md` files in the same directory
- Wrap lines to 120 characters

### Custom Line Width

```bash
python scripts/pdf_to_md.py ./pdfs --line-width 100
```

Customize the maximum line width for wrapped content.

### Disable Line Wrapping

```bash
python scripts/pdf_to_md.py ./pdfs --no-wrap
```

Output markdown without any line wrapping.

## Command-Line Options

| Option         | Description                               | Default  |
|----------------|-------------------------------------------|----------|
| `directory`    | Directory containing PDF files to process | Required |
| `--line-width` | Maximum line width for wrapping           | 120      |
| `--no-wrap`    | Disable line wrapping                     | False    |

## How It Works

1. **Initialization**: Loads docling models once with configured pipeline options
    - Disables table structure parsing (`--no-tables` equivalent)
    - Sets up image export mode to placeholder

2. **Discovery**: Finds all `.pdf` files in the specified directory and sorts them

3. **Conversion Loop**: For each PDF:
    - Converts to markdown using the pre-loaded converter
    - Wraps lines if enabled (preserving markdown structure)
    - Saves to `<filename>.md` in the same directory

4. **Summary**: Reports total processed and failed conversions

## Output Format

For each PDF file:

- Input: `document.pdf`
- Output: `document.md` (in the same directory)

## Performance

**Example**: Converting 10 PDFs

- **This script**: ~30 seconds (models loaded once)
- **CLI approach**: ~2-3 minutes (models loaded 10 times)

The performance advantage grows with the number of PDFs being processed.

## Error Handling

- Individual file failures don't stop processing
- Failed files are reported in the summary
- Press `Ctrl+C` to gracefully cancel the operation

## Requirements

- Python 3.9+
- docling library (`pip install docling`)
- opencv-python (docling dependency)

## Example Output

```
================================================================================
Batch PDF to Markdown Converter
================================================================================
Input directory: ./pdfs
Output: Markdown files will be placed in the same directory as PDFs
Line wrapping: 120 characters
================================================================================

🔧 Initializing docling converter (loading models)...
✓ Converter initialized

Found 5 PDF file(s) to process

📄 Processing: document1.pdf
✓ Successfully converted: document1.pdf -> document1.md

📄 Processing: document2.pdf
✓ Successfully converted: document2.pdf -> document2.md

...

================================================================================
Summary:
  Total processed: 5
  Total failed: 0
================================================================================
```

## See Also

- [chunk_pdf.md](chunk_pdf.md) - Split large PDFs before conversion
- [chunk_md.md](chunk_md.md) - Split large markdown files after conversion
- [translate_md.md](translate_md.md) - Translate converted markdown files
