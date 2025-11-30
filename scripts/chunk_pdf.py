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
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

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

    # Calculate number of chunks
    num_chunks = (total_pages + pages_per_chunk - 1) // pages_per_chunk

    # Display header with Rich Panel
    console = Console()
    header_text = Text()
    header_text.append(f"File: ", style="dim")
    header_text.append(f"{input_file}\n", style="cyan")
    header_text.append(f"Total pages: ", style="dim")
    header_text.append(f"{total_pages}\n", style="bold")
    header_text.append(f"Pages per chunk: ", style="dim")
    header_text.append(f"{pages_per_chunk}\n", style="bold")
    header_text.append(f"Expected chunks: ", style="dim")
    header_text.append(f"{num_chunks}", style="bold green")

    header_panel = Panel(
        header_text,
        title=f"[bold]{Icons.SPARKLES} PDF Chunking Tool[/bold]",
        border_style="cyan",
        expand=True,
        padding=(1, 2)
    )
    console.print(f"\n")
    console.print(header_panel)
    print()

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

        # Display chunk creation with Rich Panel
        chunk_text = Text()
        chunk_text.append(f"[{chunk_num}/{num_chunks}] ", style="dim")
        chunk_text.append("Chunk created: ", style="bold")
        chunk_text.append(f"{Path(output_file).name}\n", style="cyan")
        chunk_text.append(f"Pages: ", style="dim")
        chunk_text.append(f"{start_page + 1}-{end_page}", style="bold")

        chunk_panel = Panel(
            chunk_text,
            border_style="green",
            expand=True,
            padding=(0, 1)
        )
        console.print(chunk_panel)
        chunk_num += 1

    # Summary with Rich Panel
    summary_text = Text()
    summary_text.append(f"{Icons.SUCCESS} Successfully created: ", style="green")
    summary_text.append(f"{chunk_num - 1} chunks\n", style="bold green")
    summary_text.append(f"Output directory: ", style="cyan")
    summary_text.append(f"{output_dir}", style="cyan bold")

    summary_panel = Panel(
        summary_text,
        title=f"[bold]{Icons.CHART} Summary[/bold]",
        border_style="magenta",
        expand=True,
        padding=(1, 2)
    )
    console.print(f"\n")
    console.print(summary_panel)


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
