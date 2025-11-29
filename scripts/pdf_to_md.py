#!/usr/bin/env python3
"""
PDF to Markdown Converter

This script converts PDF file(s) to Markdown format using different conversion engines.
Supports both single files and batch processing of directories.

Supported engines:
- docling: Fast and efficient, loads models once for batch processing
- marker: High-quality conversion with advanced layout detection

Usage:
    # Convert a single PDF file
    python scripts/pdf_to_md.py file.pdf
    python scripts/pdf_to_md.py file.pdf --engine marker

    # Convert all PDFs in a directory
    python scripts/pdf_to_md.py <directory_path>
    python scripts/pdf_to_md.py <directory_path> --engine docling
    python scripts/pdf_to_md.py <directory_path> --line-width 120
    python scripts/pdf_to_md.py <directory_path> --no-wrap
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from utils.term import Colors, Icons
from utils.text import wrap_markdown_lines

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
    from marker.config.parser import ConfigParser
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False


def natural_sort_key(path: Path) -> list:
    """
    Generate a sort key for natural sorting of file names.
    This ensures that file10.pdf comes after file2.pdf, not before.

    Args:
        path: Path object to generate a sort key for

    Returns:
        List of strings and integers for natural sorting
    """
    return [int(c) if c.isdigit() else c.lower()
            for c in re.split(r'(\d+)', str(path.name))]


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
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} docling is not installed. Install it with: pip install docling")
        return 0, len(pdf_files)

    # Filter out PDFs that already have .md files
    files_to_process = []
    skipped = 0
    for pdf_file in pdf_files:
        md_file = pdf_file.with_suffix('.md')
        if md_file.exists():
            print(f"{Colors.YELLOW}{Icons.SKIP} Skipping:{Colors.RESET} {Colors.DIM}{pdf_file.name}{Colors.RESET} {Colors.GRAY}(markdown file already exists){Colors.RESET}")
            skipped += 1
        else:
            files_to_process.append(pdf_file)

    if not files_to_process:
        print(f"{Colors.YELLOW}{Icons.INFO} Info:{Colors.RESET} No files to convert. All PDFs already have markdown files.")
        return len(pdf_files) - skipped, 0

    if skipped > 0:
        print(f"\n{Colors.CYAN}{Icons.INFO} Found:{Colors.RESET} {Colors.BOLD}{len(pdf_files)}{Colors.RESET} PDF files ({Colors.GRAY}{skipped} already converted{Colors.RESET}, {Colors.GREEN}{len(files_to_process)} to process{Colors.RESET})\n")

    # Setup pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = False  # Equivalent to --no-tables

    # Create a converter with options (models loaded once here)
    print(f"{Colors.CYAN}{Icons.SPARKLES} Initializing docling converter {Colors.GRAY}(loading models){Colors.RESET}...")
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    print(f"{Colors.GREEN}{Icons.SUCCESS} Converter initialized{Colors.RESET}\n")

    processed = 0
    failed = 0

    for idx, pdf_file in enumerate(files_to_process):
        file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
        print(f"{Colors.BOLD}{Icons.FILE} [{idx + 1}/{len(files_to_process)}] Processing:{Colors.RESET} {Colors.CYAN}{pdf_file.name}{Colors.RESET} {Colors.GRAY}({file_size_mb:.2f} MB){Colors.RESET}")

        try:
            # Convert the PDF
            start_time = time.time()
            result = converter.convert(str(pdf_file))

            # Export to Markdown
            markdown_content = result.document.export_to_markdown()

            # Wrap lines if enabled
            if wrap_lines and line_width:
                markdown_content = wrap_markdown_lines(markdown_content, line_width)

            # Save to the same directory as the PDF
            output_file = pdf_file.with_suffix('.md')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            elapsed = time.time() - start_time
            print(f"{Colors.GREEN}{Icons.SUCCESS} Successfully converted:{Colors.RESET} {Colors.CYAN}{pdf_file.name}{Colors.RESET} {Icons.ARROW} {Colors.CYAN}{output_file.name}{Colors.RESET} {Colors.GRAY}({Icons.CLOCK} {elapsed:.2f}s){Colors.RESET}")
            processed += 1

        except Exception as e:
            print(f"{Colors.RED}{Icons.ERROR} Failed to process {Colors.CYAN}{pdf_file.name}{Colors.RESET}: {Colors.RED}{e}{Colors.RESET}")
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
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} marker is not installed. Install it with: pip install marker-pdf")
        return 0, len(pdf_files)

    # Filter out PDFs that already have .md files
    files_to_process = []
    skipped = 0
    for pdf_file in pdf_files:
        md_file = pdf_file.with_suffix('.md')
        if md_file.exists():
            print(f"{Colors.YELLOW}{Icons.SKIP} Skipping:{Colors.RESET} {Colors.DIM}{pdf_file.name}{Colors.RESET} {Colors.GRAY}(markdown file already exists){Colors.RESET}")
            skipped += 1
        else:
            files_to_process.append(pdf_file)

    if not files_to_process:
        print(f"{Colors.YELLOW}{Icons.INFO} Info:{Colors.RESET} No files to convert. All PDFs already have markdown files.")
        return len(pdf_files) - skipped, 0

    if skipped > 0:
        print(f"\n{Colors.CYAN}{Icons.INFO} Found:{Colors.RESET} {Colors.BOLD}{len(pdf_files)}{Colors.RESET} PDF files ({Colors.GRAY}{skipped} already converted{Colors.RESET}, {Colors.GREEN}{len(files_to_process)} to process{Colors.RESET})\n")

    # Initialize marker converter (models loaded once here)
    print(f"{Colors.CYAN}{Icons.SPARKLES} Initializing marker converter {Colors.GRAY}(loading models){Colors.RESET}...")
    try:
        config = {
            # "disable_image_extraction": "true",
        }
        converter = PdfConverter(
            artifact_dict=create_model_dict(),
            config=ConfigParser(config).generate_config_dict()
        )
        print(f"{Colors.GREEN}{Icons.SUCCESS} Converter initialized{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.RED}{Icons.ERROR} Error initializing marker converter: {Colors.RED}{e}{Colors.RESET}")
        return 0, len(pdf_files)

    processed = 0
    failed = 0

    for idx, pdf_file in enumerate(files_to_process):
        file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
        print(f"{Colors.BOLD}{Icons.FILE} [{idx + 1}/{len(files_to_process)}] Processing:{Colors.RESET} {Colors.CYAN}{pdf_file.name}{Colors.RESET} {Colors.GRAY}({file_size_mb:.2f} MB){Colors.RESET}")

        try:
            # Convert the PDF
            start_time = time.time()
            rendered = converter(str(pdf_file))

            # Extract Markdown text
            markdown_content, _, _ = text_from_rendered(rendered)

            # Wrap lines if enabled
            if wrap_lines and line_width:
                markdown_content = wrap_markdown_lines(markdown_content, line_width)

            # Save to the same directory as the PDF
            output_file = pdf_file.with_suffix('.md')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            elapsed = time.time() - start_time
            print(f"{Colors.GREEN}{Icons.SUCCESS} Successfully converted:{Colors.RESET} {Colors.CYAN}{pdf_file.name}{Colors.RESET} {Icons.ARROW} {Colors.CYAN}{output_file.name}{Colors.RESET} {Colors.GRAY}({Icons.CLOCK} {elapsed:.2f}s){Colors.RESET}")
            processed += 1

        except Exception as e:
            print(f"{Colors.RED}{Icons.ERROR} Failed to process {Colors.CYAN}{pdf_file.name}{Colors.RESET}: {Colors.RED}{e}{Colors.RESET}")
            failed += 1

        print()

    return processed, failed


def process_pdfs(
        input_path: str,
        engine: str = "docling",
        line_width: Optional[int] = 120,
        wrap_lines: bool = True
) -> tuple[int, int]:
    """
    Process PDF file(s) and convert them to Markdown.

    Args:
        input_path: Path to a PDF file or directory containing PDF files
        engine: Conversion engine to use ("docling" or "marker")
        line_width: Maximum line width for wrapping (default: 120)
        wrap_lines: Whether to wrap lines (default: True)

    Returns:
        Tuple of (processed_count, failed_count)
    """
    # Determine if the input is a file or directory
    path = Path(input_path)

    if path.is_file():
        # Single file mode
        if path.suffix.lower() != '.pdf':
            print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} {input_path} is not a PDF file")
            return 0, 1
        pdf_files = [path]
    elif path.is_dir():
        # Directory mode - find all PDF files
        pdf_files = sorted(path.glob("*.pdf"), key=natural_sort_key)
        if not pdf_files:
            print(f"{Colors.YELLOW}{Icons.INFO} Info:{Colors.RESET} No PDF files found in {input_path}")
            return 0, 0
    else:
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} {input_path} is not a valid file or directory")
        return 0, 1

    print(f"{Colors.CYAN}{Icons.INFO} Found:{Colors.RESET} {Colors.BOLD}{len(pdf_files)}{Colors.RESET} PDF file(s) to process\n")

    # Process using the selected engine
    if engine == "docling":
        return process_pdfs_with_docling(pdf_files, line_width, wrap_lines)
    elif engine == "marker":
        return process_pdfs_with_marker(pdf_files, line_width, wrap_lines)
    else:
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} Unknown engine '{engine}'. Supported engines: docling, marker")
        return 0, len(pdf_files)


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF file(s) to Markdown using various engines",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input",
        help="Path to a PDF file or directory containing PDF files to process"
    )

    parser.add_argument(
        "-e", "--engine",
        choices=["docling", "marker"],
        default="marker",
        help="PDF to Markdown conversion engine (default: marker)"
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

    # Validate input path exists
    if not os.path.exists(args.input):
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} '{args.input}' does not exist")
        sys.exit(1)

    # Check if the selected engine is available
    if args.engine == "docling" and not DOCLING_AVAILABLE:
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} docling is not installed. Install it with: pip install docling")
        print(f"{Colors.GRAY}Or use a different engine with --engine marker{Colors.RESET}")
        sys.exit(1)
    elif args.engine == "marker" and not MARKER_AVAILABLE:
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} marker is not installed. Install it with: pip install marker-pdf")
        print(f"{Colors.GRAY}Or use a different engine with --engine docling{Colors.RESET}")
        sys.exit(1)

    # Determine the input type for display
    input_path = Path(args.input)
    input_type = "file" if input_path.is_file() else "directory"

    print(f"{Colors.CYAN}{'─' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Icons.SPARKLES} PDF to Markdown Converter{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 80}{Colors.RESET}")
    print(f"  {Colors.DIM}Input {input_type}:{Colors.RESET} {Colors.CYAN}{args.input}{Colors.RESET}")
    print(f"  {Colors.DIM}Engine:{Colors.RESET} {Colors.MAGENTA}{args.engine}{Colors.RESET}")
    print(f"  {Colors.DIM}Output:{Colors.RESET} Markdown files will be placed in the same directory as PDFs")
    if args.no_wrap:
        print(f"  {Colors.DIM}Line wrapping:{Colors.RESET} {Colors.YELLOW}Disabled{Colors.RESET}")
    else:
        print(f"  {Colors.DIM}Line wrapping:{Colors.RESET} {Colors.GREEN}{args.line_width} characters{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 80}{Colors.RESET}\n")

    batch_start_time = time.time()
    processed, failed = process_pdfs(
        args.input,
        engine=args.engine,
        line_width=args.line_width,
        wrap_lines=not args.no_wrap
    )
    total_time = time.time() - batch_start_time

    # Summary
    print(f"\n{Colors.MAGENTA}{'═' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Icons.CHART} Summary{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'═' * 80}{Colors.RESET}")
    print(f"  {Colors.CYAN}Total processed:{Colors.RESET} {Colors.BOLD}{Colors.GREEN}{processed}{Colors.RESET}")
    if failed > 0:
        print(f"  {Colors.RED}{Icons.ERROR} Total failed:{Colors.RESET} {Colors.BOLD}{Colors.RED}{failed}{Colors.RESET}")
    print(f"  {Colors.CYAN}Total time:{Colors.RESET} {Colors.BOLD}{total_time:.2f}s{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'═' * 80}{Colors.RESET}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Conversion cancelled by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
