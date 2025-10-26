#!/usr/bin/env python3
"""
Batch PDF to Markdown Converter using Docling

This script converts all PDF files in a directory to Markdown format using docling's
Python API. Unlike the bash script version, this loads the docling models only once,
making it much more efficient for processing multiple files.

Usage:
    python scripts/batch_convert_pdf_to_md.py <directory_path>
    python scripts/batch_convert_pdf_to_md.py <directory_path> --line-width 120
    python scripts/batch_convert_pdf_to_md.py <directory_path> --no-wrap
"""

import argparse
import os
import sys
import textwrap
from pathlib import Path
from typing import Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter
from docling.document_converter import PdfFormatOption


def wrap_markdown_lines(content: str, width: int = 120) -> str:
    """
    Wrap markdown lines to a specified width while preserving structure.

    Args:
        content: The markdown content
        width: Maximum line width (default: 120)

    Returns:
        Wrapped markdown content
    """
    lines = content.split('\n')
    wrapped_lines = []

    for line in lines:
        # Don't wrap empty lines, headers, code blocks, or lines that are already short
        if (not line.strip() or
                line.strip().startswith('#') or
                line.strip().startswith('```') or
                line.strip().startswith('|') or  # Tables
                len(line) <= width):
            wrapped_lines.append(line)
        else:
            # Wrap long lines
            wrapped = textwrap.fill(
                line,
                width=width,
                break_long_words=False,
                break_on_hyphens=False
            )
            wrapped_lines.append(wrapped)

    return '\n'.join(wrapped_lines)


def process_pdfs(
        directory: str,
        line_width: Optional[int] = 120,
        wrap_lines: bool = True
) -> tuple[int, int]:
    """
    Process all PDF files in a directory and convert them to Markdown.

    Args:
        directory: Directory containing PDF files
        line_width: Maximum line width for wrapping (default: 120)
        wrap_lines: Whether to wrap lines (default: True)

    Returns:
        Tuple of (processed_count, failed_count)
    """
    # Setup pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = False  # Equivalent to --no-tables

    # Create converter with options (models loaded once here)
    print("🔧 Initializing docling converter (loading models)...")
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    print("✓ Converter initialized\n")

    # Find all PDF files
    pdf_dir = Path(directory)
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return 0, 0

    print(f"Found {len(pdf_files)} PDF file(s) to process\n")

    processed = 0
    failed = 0

    for pdf_file in pdf_files:
        print(f"📄 Processing: {pdf_file.name}")

        try:
            # Convert the PDF
            result = converter.convert(str(pdf_file))

            # Export to markdown
            markdown_content = result.document.export_to_markdown()

            # Wrap lines if enabled
            if wrap_lines and line_width:
                markdown_content = wrap_markdown_lines(markdown_content, line_width)

            # Save to the same directory as the PDF
            output_file = pdf_file.with_suffix('.md')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"✓ Successfully converted: {pdf_file.name} -> {output_file.name}")
            processed += 1

        except Exception as e:
            print(f"✗ Failed to process {pdf_file.name}: {e}")
            failed += 1

        print()

    return processed, failed


def main():
    parser = argparse.ArgumentParser(
        description="Batch convert PDF files to Markdown using docling",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "directory",
        help="Directory containing PDF files to process"
    )

    parser.add_argument(
        "--line-width",
        type=int,
        default=120,
        help="Maximum line width for wrapping (default: 120)"
    )

    parser.add_argument(
        "--no-wrap",
        action="store_true",
        help="Disable line wrapping"
    )

    args = parser.parse_args()

    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)

    print("=" * 80)
    print("Batch PDF to Markdown Converter")
    print("=" * 80)
    print(f"Input directory: {args.directory}")
    print(f"Output: Markdown files will be placed in the same directory as PDFs")
    if args.no_wrap:
        print(f"Line wrapping: Disabled")
    else:
        print(f"Line wrapping: {args.line_width} characters")
    print("=" * 80)
    print()

    processed, failed = process_pdfs(
        args.directory,
        line_width=args.line_width,
        wrap_lines=not args.no_wrap
    )

    # Summary
    print("=" * 80)
    print("Summary:")
    print(f"  Total processed: {processed}")
    if failed > 0:
        print(f"  Total failed: {failed}")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Translation cancelled by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
