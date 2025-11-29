#!/usr/bin/env python3
"""
PDF Chunking Script

This script splits a PDF file into smaller chunks based on the number of pages per chunk.

Usage:
python scripts/chunk_pdf.py workspace/book/book.pdf
"""

import argparse
import os
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from utils.term import Colors, Icons


def chunk_pdf(input_file: str, output_dir: str, pages_per_chunk: int = 10):
    """
    Split a PDF file into chunks.

    Args:
        input_file: Path to the input PDF file
        output_dir: Directory where chunks will be saved
        pages_per_chunk: Number of pages per chunk (default: 10)
    """
    # Validate input file
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Read the PDF
    reader = PdfReader(input_file)
    total_pages = len(reader.pages)

    print(f"\n{Colors.CYAN}{'─' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Icons.FILE} Processing PDF{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 80}{Colors.RESET}")
    print(f"  {Colors.DIM}File:{Colors.RESET} {Colors.CYAN}{input_file}{Colors.RESET}")
    print(f"  {Colors.DIM}Total pages:{Colors.RESET} {Colors.BOLD}{total_pages}{Colors.RESET}")
    print(f"  {Colors.DIM}Pages per chunk:{Colors.RESET} {Colors.BOLD}{pages_per_chunk}{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 80}{Colors.RESET}\n")

    # Get base filename without extension
    base_name = Path(input_file).stem

    # Split into chunks
    chunk_num = 1
    for start_page in range(0, total_pages, pages_per_chunk):
        end_page = min(start_page + pages_per_chunk, total_pages)

        # Create a new PDF writer for this chunk
        writer = PdfWriter()

        # Add pages to this chunk
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])

        # Save the chunk
        output_file = os.path.join(
            output_dir,
            f"{base_name}_chunk_{chunk_num:03d}_pages_{start_page + 1}-{end_page}.pdf"
        )

        with open(output_file, "wb") as output_pdf:
            writer.write(output_pdf)

        print(
            f"{Colors.GREEN}{Icons.SUCCESS} Created chunk {Colors.BOLD}{chunk_num}{Colors.RESET}: {Colors.CYAN}{output_file}{Colors.RESET} {Colors.GRAY}(pages {start_page + 1}-{end_page}){Colors.RESET}")
        chunk_num += 1

    print(f"\n{Colors.MAGENTA}{'═' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Icons.CHART} Summary{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'═' * 80}{Colors.RESET}")
    print(
        f"  {Colors.GREEN}{Icons.SUCCESS} Successfully created:{Colors.RESET} {Colors.BOLD}{Colors.GREEN}{chunk_num - 1}{Colors.RESET} chunks")
    print(f"  {Colors.CYAN}Output directory:{Colors.RESET} {Colors.CYAN}{output_dir}{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'═' * 80}{Colors.RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Split a PDF file into smaller chunks",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input_file",
        help="Path to the input PDF file"
    )

    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Output directory for PDF chunks (default: 'chunks' folder in the same directory as the input PDF)"
    )

    parser.add_argument(
        "-p", "--pages-per-chunk",
        type=int,
        default=10,
        help="Number of pages per chunk"
    )

    args = parser.parse_args()

    # If no output directory specified, create a 'chunks' folder next to the input PDF
    if args.output_dir is None:
        input_path = Path(args.input_file)
        args.output_dir = str(input_path.parent / "chunks")

    try:
        chunk_pdf(args.input_file, args.output_dir, args.pages_per_chunk)
    except Exception as e:
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} {e}")
        exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Translation cancelled by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
