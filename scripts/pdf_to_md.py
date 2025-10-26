#!/usr/bin/env python3
"""
Batch PDF to Markdown Converter

This script converts all PDF files in a directory to Markdown format using different
conversion engines. Supported engines:
- docling: Fast and efficient, loads models once for batch processing
- marker: High-quality conversion with advanced layout detection

Usage:
    python scripts/pdf_to_md.py <directory_path>
    python scripts/pdf_to_md.py <directory_path> --engine marker
    python scripts/pdf_to_md.py <directory_path> --line-width 120
    python scripts/pdf_to_md.py <directory_path> --no-wrap
"""

import argparse
import os
import sys
import textwrap
from pathlib import Path
from typing import Optional

# Docling imports
try:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter
    from docling.document_converter import PdfFormatOption
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Marker imports
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False


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


def process_pdfs_with_docling(
        pdf_files: list[Path],
        line_width: Optional[int] = 120,
        wrap_lines: bool = True
) -> tuple[int, int]:
    """
    Process PDF files using the docling engine.

    Args:
        pdf_files: List of PDF file paths to process
        line_width: Maximum line width for wrapping (default: 120)
        wrap_lines: Whether to wrap lines (default: True)

    Returns:
        Tuple of (processed_count, failed_count)
    """
    if not DOCLING_AVAILABLE:
        print("Error: docling is not installed. Install it with: pip install docling")
        return 0, len(pdf_files)

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


def process_pdfs_with_marker(
        pdf_files: list[Path],
        line_width: Optional[int] = 120,
        wrap_lines: bool = True
) -> tuple[int, int]:
    """
    Process PDF files using the marker engine.

    Args:
        pdf_files: List of PDF file paths to process
        line_width: Maximum line width for wrapping (default: 120)
        wrap_lines: Whether to wrap lines (default: True)

    Returns:
        Tuple of (processed_count, failed_count)
    """
    if not MARKER_AVAILABLE:
        print("Error: marker is not installed. Install it with: pip install marker-pdf")
        return 0, len(pdf_files)

    # Initialize marker converter (models loaded once here)
    print("🔧 Initializing marker converter (loading models)...")
    try:
        converter = PdfConverter(
            artifact_dict=create_model_dict(),
        )
        print("✓ Converter initialized\n")
    except Exception as e:
        print(f"Error initializing marker converter: {e}")
        return 0, len(pdf_files)

    processed = 0
    failed = 0

    for pdf_file in pdf_files:
        print(f"📄 Processing: {pdf_file.name}")

        try:
            # Convert the PDF
            rendered = converter(str(pdf_file))

            # Extract markdown text
            markdown_content, _, _ = text_from_rendered(rendered)

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


def process_pdfs(
        directory: str,
        engine: str = "docling",
        line_width: Optional[int] = 120,
        wrap_lines: bool = True
) -> tuple[int, int]:
    """
    Process all PDF files in a directory and convert them to Markdown.

    Args:
        directory: Directory containing PDF files
        engine: Conversion engine to use ("docling" or "marker")
        line_width: Maximum line width for wrapping (default: 120)
        wrap_lines: Whether to wrap lines (default: True)

    Returns:
        Tuple of (processed_count, failed_count)
    """
    # Find all PDF files
    pdf_dir = Path(directory)
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return 0, 0

    print(f"Found {len(pdf_files)} PDF file(s) to process\n")

    # Process using the selected engine
    if engine == "docling":
        return process_pdfs_with_docling(pdf_files, line_width, wrap_lines)
    elif engine == "marker":
        return process_pdfs_with_marker(pdf_files, line_width, wrap_lines)
    else:
        print(f"Error: Unknown engine '{engine}'. Supported engines: docling, marker")
        return 0, len(pdf_files)


def main():
    parser = argparse.ArgumentParser(
        description="Batch convert PDF files to Markdown using various engines",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "directory",
        help="Directory containing PDF files to process"
    )

    parser.add_argument(
        "-e", "--engine",
        choices=["docling", "marker"],
        default="marker",
        help="PDF to Markdown conversion engine (default: docling)"
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

    # Check if selected engine is available
    if args.engine == "docling" and not DOCLING_AVAILABLE:
        print("Error: docling is not installed. Install it with: pip install docling")
        print("Or use a different engine with --engine marker")
        sys.exit(1)
    elif args.engine == "marker" and not MARKER_AVAILABLE:
        print("Error: marker is not installed. Install it with: pip install marker-pdf")
        print("Or use a different engine with --engine docling")
        sys.exit(1)

    print("=" * 80)
    print("Batch PDF to Markdown Converter")
    print("=" * 80)
    print(f"Input directory: {args.directory}")
    print(f"Engine: {args.engine}")
    print(f"Output: Markdown files will be placed in the same directory as PDFs")
    if args.no_wrap:
        print(f"Line wrapping: Disabled")
    else:
        print(f"Line wrapping: {args.line_width} characters")
    print("=" * 80)
    print()

    processed, failed = process_pdfs(
        args.directory,
        engine=args.engine,
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
