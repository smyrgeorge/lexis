#!/usr/bin/env python3
"""
PDF to Markdown Converter

This script converts PDF file(s) to Markdown format using marker.
Supports both single files and batch processing of directories.

Usage:
    # Convert a single PDF file
    python scripts/pdf_to_md.py file.pdf

    # Convert all PDFs in a directory
    python scripts/pdf_to_md.py <directory_path>
    python scripts/pdf_to_md.py <directory_path> --line-width 120
    python scripts/pdf_to_md.py <directory_path> --no-wrap
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import save_output
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from utils.file import natural_sort_key
from utils.term import Colors, Icons
from utils.text import wrap_markdown_lines


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

    console = Console()
    for idx, pdf_file in enumerate(files_to_process):
        file_size_mb = pdf_file.stat().st_size / (1024 * 1024)

        # Display file processing header with Rich Panel
        header_text = Text()
        header_text.append(f"{Icons.FILE} ", style="bold")
        header_text.append(f"[{idx + 1}/{len(files_to_process)}] ", style="dim")
        header_text.append("Processing: ", style="bold")
        header_text.append(f"{pdf_file.name}\n", style="cyan bold")
        header_text.append(f"Size: ", style="dim")
        header_text.append(f"{file_size_mb:.2f} MB", style="bold")

        header_panel = Panel(
            header_text,
            border_style="blue",
            expand=True,
            padding=(0, 1)
        )
        console.print(header_panel)

        try:
            # Convert the PDF
            start_time = time.time()
            rendered = converter(str(pdf_file))

            # Save Markdown and images to the same directory as the PDF
            output_dir = str(pdf_file.parent)
            output_basename = pdf_file.stem

            # Use marker's save_output to handle both text and images
            save_output(rendered, output_dir, output_basename)

            # If line wrapping is enabled, read the generated Markdown and re-wrap it
            output_file = pdf_file.with_suffix('.md')
            if wrap_lines and line_width:
                with open(output_file, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                markdown_content = wrap_markdown_lines(markdown_content, line_width)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

            elapsed = time.time() - start_time
            # Count images by checking if an images directory was created
            images_dir = pdf_file.parent / f"{output_basename}_images"
            image_count = len(list(images_dir.glob('*'))) if images_dir.exists() else 0

            print(f"{Colors.GREEN}{Icons.SUCCESS} Successfully converted:{Colors.RESET} {Colors.CYAN}{pdf_file.name}{Colors.RESET} {Icons.ARROW} {Colors.CYAN}{output_file.name}{Colors.RESET} {Colors.GRAY}({image_count} images, {Icons.CLOCK} {elapsed:.2f}s){Colors.RESET}")
            processed += 1

        except Exception as e1:
            print(f"{Colors.RED}{Icons.ERROR} Failed to process {Colors.CYAN}{pdf_file.name}{Colors.RESET}: {Colors.RED}{e1}{Colors.RESET}")
            failed += 1

        print()

    return processed, failed


def process_pdfs(
        input_path: str,
        line_width: Optional[int] = 120,
        wrap_lines: bool = True
) -> tuple[int, int]:
    """
    Process PDF file(s) and convert them to Markdown.

    Args:
        input_path: Path to a PDF file or directory containing PDF files
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

    return process_pdfs_with_marker(pdf_files, line_width, wrap_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF file(s) to Markdown using marker",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input",
        help="Path to a PDF file or directory containing PDF files to process"
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

    # Determine the input type for display
    input_path = Path(args.input)
    input_type = "file" if input_path.is_file() else "directory"

    # Display header with Rich Panel
    console = Console()
    header_text = Text()
    header_text.append(f"Input {input_type}: ", style="dim")
    header_text.append(f"{args.input}\n", style="cyan")
    header_text.append(f"Output: ", style="dim")
    header_text.append(f"Markdown files will be placed in the same directory as PDFs\n", style="")
    header_text.append(f"Line wrapping: ", style="dim")
    if args.no_wrap:
        header_text.append(f"Disabled", style="yellow")
    else:
        header_text.append(f"{args.line_width} characters", style="green")

    header_panel = Panel(
        header_text,
        title=f"[bold]{Icons.SPARKLES} PDF to Markdown Converter[/bold]",
        border_style="cyan",
        expand=True,
        padding=(1, 2)
    )
    console.print(f"\n")
    console.print(header_panel)
    print()

    batch_start_time = time.time()
    processed, failed = process_pdfs(
        args.input,
        line_width=args.line_width,
        wrap_lines=not args.no_wrap
    )
    total_time = time.time() - batch_start_time

    # Summary with Rich Panel
    summary_text = Text()
    summary_text.append(f"Total processed: ", style="cyan")
    summary_text.append(f"{processed}\n", style="bold green")
    if failed > 0:
        summary_text.append(f"{Icons.ERROR} Total failed: ", style="red")
        summary_text.append(f"{failed}\n", style="bold red")
    summary_text.append(f"Total time: ", style="cyan")
    summary_text.append(f"{total_time:.2f}s", style="bold")

    summary_panel = Panel(
        summary_text,
        title=f"[bold]{Icons.CHART} Summary[/bold]",
        border_style="magenta",
        expand=True,
        padding=(1, 2)
    )
    console.print(f"\n")
    console.print(summary_panel)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Conversion cancelled by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
