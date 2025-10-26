#!/usr/bin/env python3
"""
PDF Chunking Script

This script splits a PDF file into smaller chunks based on the number of pages per chunk.

python scripts/chunk_pdf.py workspace/my-book/my-book.pdf
"""

import argparse
import os
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


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

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Read the PDF
    reader = PdfReader(input_file)
    total_pages = len(reader.pages)

    print(f"Processing PDF: {input_file}")
    print(f"Total pages: {total_pages}")
    print(f"Pages per chunk: {pages_per_chunk}")

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

        print(f"Created chunk {chunk_num}: {output_file} (pages {start_page + 1}-{end_page})")
        chunk_num += 1

    print(f"\nSuccessfully created {chunk_num - 1} chunks in {output_dir}")


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

    # If no output directory specified, create 'chunks' folder next to the input PDF
    if args.output_dir is None:
        input_path = Path(args.input_file)
        args.output_dir = str(input_path.parent / "chunks")

    try:
        chunk_pdf(args.input_file, args.output_dir, args.pages_per_chunk)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Translation cancelled by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
