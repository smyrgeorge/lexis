# chunk_pdf.py

Splits large PDF files into smaller chunks based on page count.

## Overview

This script divides a PDF file into multiple smaller PDF files, each containing a specified number of pages. This is
useful for:

- Processing large documents in manageable pieces
- Parallel processing of different sections
- Working around file size limitations
- Creating logical document divisions

## Key Features

- **Flexible Page Count**: Configurable pages per chunk (default: 10)
- **Custom Output Directory**: Specify where chunks should be saved
- **Descriptive Naming**: Chunks are named with page ranges for easy identification
- **Automatic Directory Creation**: Output directory is created if it doesn't exist
- **Page Range Tracking**: Filenames include the exact page range of each chunk

## Usage

### Basic Usage

```bash
python scripts/chunk_pdf.py input.pdf
```

This will:

- Split `input.pdf` into chunks of 10 pages each
- Save chunks to `./pdf_chunks/` directory
- Name chunks like `input_chunk_001_pages_1-10.pdf`

### Custom Pages Per Chunk

```bash
python scripts/chunk_pdf.py document.pdf -p 20
```

Split into chunks of 20 pages each.

### Custom Output Directory

```bash
python scripts/chunk_pdf.py document.pdf -o ./my-chunks
```

Save chunks to a custom directory.

### Complete Example

```bash
python scripts/chunk_pdf.py large-book.pdf -p 15 -o ./book-chunks
```

Split `large-book.pdf` into 15-page chunks and save to `./book-chunks/`.

## Command-Line Options

| Option              | Short | Description                     | Default            |
|---------------------|-------|---------------------------------|--------------------|
| `input_file`        | -     | Path to the input PDF file      | Required           |
| `--output-dir`      | `-o`  | Output directory for PDF chunks | `./out/pdf-chunks` |
| `--pages-per-chunk` | `-p`  | Number of pages per chunk       | 10                 |

## How It Works

1. **Validation**: Checks that the input PDF file exists
2. **Reading**: Opens and reads the PDF file using pypdf
3. **Chunking**: Divides pages into groups of the specified size
4. **Writing**: For each chunk:
    - Creates a new PDF with those pages
    - Generates a descriptive filename with page range
    - Saves to the output directory

## Output Format

Chunks are named with a consistent format:

```
<base_name>_chunk_<number>_pages_<start>-<end>.pdf
```

**Examples**:

- `document_chunk_001_pages_1-10.pdf`
- `document_chunk_002_pages_11-20.pdf`
- `document_chunk_003_pages_21-25.pdf` (last chunk may have fewer pages)

## Use Cases

### 1. Large Document Translation Pipeline

```bash
# Step 1: Split large PDF into chunks
python scripts/chunk_pdf.py large-document.pdf -p 10 -o ./chunks

# Step 2: Convert chunks to markdown
python scripts/pdf_to_md.py ./chunks

# Step 3: Translate markdown chunks
python scripts/translate_md.py ./chunks -s Spanish -t English
```

### 2. Parallel Processing

Split a 200-page PDF into 10-page chunks, then process chunks in parallel on different machines or processors.

### 3. Section-Based Division

```bash
# Split by chapter (assuming ~50 pages per chapter)
python scripts/chunk_pdf.py book.pdf -p 50 -o ./chapters
```

## Requirements

- Python 3.9+
- pypdf library (`pip install pypdf`)

## Example Output

```
Processing PDF: large-document.pdf
Total pages: 47
Pages per chunk: 10

Created chunk 1: ./pdf_chunks/large-document_chunk_001_pages_1-10.pdf (pages 1-10)
Created chunk 2: ./pdf_chunks/large-document_chunk_002_pages_11-20.pdf (pages 11-20)
Created chunk 3: ./pdf_chunks/large-document_chunk_003_pages_21-30.pdf (pages 21-30)
Created chunk 4: ./pdf_chunks/large-document_chunk_004_pages_31-40.pdf (pages 31-40)
Created chunk 5: ./pdf_chunks/large-document_chunk_005_pages_41-47.pdf (pages 41-47)

Successfully created 5 chunks in ./pdf_chunks
```

## Error Handling

The script will display an error and exit if:

- Input file doesn't exist
- Input file is not a valid PDF
- pypdf library is not installed

## Tips

- **Optimal Chunk Size**: 10-20 pages works well for most translation workflows
- **Memory Usage**: Smaller chunks use less memory during processing
- **Naming**: Keep original PDF name descriptive; it's used in chunk filenames

## See Also

- [batch_convert_pdf_to_md.md](pdf_to_md.md) - Convert chunked PDFs to markdown
- [chunk_md.md](chunk_md.md) - Alternative: chunk after conversion to markdown
- [translate_md.md](translate_md.md) - Translate the resulting markdown chunks
