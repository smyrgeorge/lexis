#!/usr/bin/env python3
"""
Complete Translation Pipeline

This script orchestrates the entire workflow:
1. Validates and locates PDF in workspace subdirectory
2. Splits PDF into chunks
3. Converts chunks to Markdown
4. Translates Markdown files to target language

The PDF must be located in a subdirectory under the workspace folder.
PDF filenames must contain only alphanumeric characters, dashes, and .pdf extension.

Usage:
    python scripts/pipeline.py project-name/document.pdf -s Spanish -t English
    python scripts/pipeline.py my-book/book.pdf -s Spanish -t English -p 15
    python scripts/pipeline.py project/doc.pdf -s es -t en --provider openai
    python scripts/pipeline.py project/doc.pdf -s es -t en --skip-chunking
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
WORKSPACE_DIR = PROJECT_ROOT / "workspace"


def validate_pdf_filename(filename: str) -> bool:
    """
    Validate PDF filename.

    Args:
        filename: The PDF filename to validate

    Returns:
        True if valid, False otherwise
    """
    # Pattern: alphanumeric, dashes, underscores, and .pdf extension
    # Examples: book.pdf, my-book.pdf, book_2024.pdf
    pattern = r'^[a-zA-Z0-9_-]+\.pdf$'
    return bool(re.match(pattern, filename))


def validate_pdf_path(pdf_path: str) -> tuple[bool, str]:
    """
    Validate that PDF path is in workspace subdirectory and filename is valid.

    Args:
        pdf_path: Relative path to PDF (e.g., 'project/book.pdf')

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(pdf_path)

    # Check if path has at least one parent directory
    if not path.parent or path.parent == Path('.'):
        return False, "PDF must be in a subdirectory (e.g., 'project-name/document.pdf')"

    # Validate filename
    filename = path.name
    if not validate_pdf_filename(filename):
        return False, (
            f"Invalid PDF filename: '{filename}'\n"
            "Filename must contain only letters, numbers, dashes, underscores, and .pdf extension\n"
            "Examples: book.pdf, my-book.pdf, document_2024.pdf"
        )

    # Construct full path
    full_path = WORKSPACE_DIR / path

    # Check if file exists
    if not full_path.exists():
        return False, f"PDF file not found: {full_path}"

    if not full_path.is_file():
        return False, f"Path is not a file: {full_path}"

    return True, ""


def run_command(cmd: list[str], description: str) -> int:
    """
    Run a command and display output in real-time.

    Args:
        cmd: Command and arguments as list
        description: Description of what the command does

    Returns:
        Return code from the command
    """
    print(f"\n{'=' * 80}")
    print(f"STEP: {description}")
    print(f"{'=' * 80}")
    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\n✗ Command failed with exit code {result.returncode}")
    else:
        print(f"\n✓ Step completed successfully")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Complete PDF translation pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="""
Examples:
  python scripts/pipeline.py project/book.pdf -s Spanish -t English
  python scripts/pipeline.py my-docs/manual.pdf -s es -t en -p 20
  python scripts/pipeline.py work/document.pdf -s Spanish -t English --provider openai
  python scripts/pipeline.py project/doc.pdf -s es -t en --skip-chunking
        """
    )

    parser.add_argument(
        "pdf_path",
        help="Relative path to PDF under workspace directory (e.g., 'project/document.pdf')"
    )

    parser.add_argument(
        "-s", "--source-lang",
        required=True,
        help="Source language (e.g., 'Spanish', 'es')"
    )

    parser.add_argument(
        "-t", "--target-lang",
        required=True,
        help="Target language (e.g., 'English', 'en')"
    )

    parser.add_argument(
        "-p", "--pages-per-chunk",
        type=int,
        default=10,
        help="Number of pages per chunk for PDF splitting"
    )

    parser.add_argument(
        "--provider",
        choices=["claude", "openai"],
        default="claude",
        help="LLM provider for translation"
    )

    parser.add_argument(
        "--model",
        help="Specific model to use (overrides provider default)"
    )

    parser.add_argument(
        "--line-width",
        type=int,
        default=120,
        help="Line width for markdown wrapping"
    )

    parser.add_argument(
        "--no-wrap",
        action="store_true",
        help="Disable line wrapping in markdown conversion"
    )

    parser.add_argument(
        "-c", "--context-lines",
        type=int,
        default=5,
        help="Number of context lines from adjacent chunks for translation"
    )

    parser.add_argument(
        "-d", "--dictionary",
        help="Path to CSV dictionary file for specialized terminology"
    )

    parser.add_argument(
        "--skip-chunking",
        action="store_true",
        help="Skip PDF chunking (convert entire PDF directly)"
    )

    args = parser.parse_args()

    # Validate PDF path
    is_valid, error_msg = validate_pdf_path(args.pdf_path)
    if not is_valid:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)

    # Setup paths
    pdf_path = WORKSPACE_DIR / args.pdf_path
    project_dir = pdf_path.parent
    pdf_name = pdf_path.stem

    print("=" * 80)
    print("LEXIS TRANSLATION PIPELINE")
    print("=" * 80)
    print(f"PDF File: {pdf_path}")
    print(f"Project Directory: {project_dir}")
    print(f"Source Language: {args.source_lang}")
    print(f"Target Language: {args.target_lang}")
    print(f"Provider: {args.provider}")
    if args.skip_chunking:
        print(f"Mode: Direct conversion (no chunking)")
    else:
        print(f"Pages per chunk: {args.pages_per_chunk}")
    print("=" * 80)

    try:
        # Step 1: Chunk PDF (unless skipped)
        if args.skip_chunking:
            print("\n⊘ Skipping PDF chunking (processing entire PDF)")
            chunks_dir = project_dir
            pdf_to_convert = str(pdf_path)
        else:
            chunks_dir = project_dir / "chunks"

            chunk_cmd = [
                sys.executable,
                str(SCRIPTS_DIR / "chunk_pdf.py"),
                str(pdf_path),
                "-o", str(chunks_dir),
                "-p", str(args.pages_per_chunk)
            ]

            returncode = run_command(
                chunk_cmd,
                f"Splitting PDF into chunks ({args.pages_per_chunk} pages each)"
            )

            if returncode != 0:
                print("\n✗ Pipeline failed at PDF chunking step")
                sys.exit(1)

        # Step 2: Convert PDFs to Markdown
        convert_cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "batch_convert_pdf_to_md.py"),
            str(chunks_dir if not args.skip_chunking else project_dir)
        ]

        if args.no_wrap:
            convert_cmd.append("--no-wrap")
        else:
            convert_cmd.extend(["--line-width", str(args.line_width)])

        returncode = run_command(
            convert_cmd,
            "Converting PDFs to Markdown"
        )

        if returncode != 0:
            print("\n✗ Pipeline failed at PDF-to-Markdown conversion step")
            sys.exit(1)

        # Step 3: Translate Markdown files
        translate_cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "translate_md.py"),
            str(chunks_dir if not args.skip_chunking else f"{project_dir}/{pdf_name}.md"),
            "-s", args.source_lang,
            "-t", args.target_lang,
            "--provider", args.provider,
            "-c", str(args.context_lines)
        ]

        if args.model:
            translate_cmd.extend(["-m", args.model])

        if args.dictionary:
            translate_cmd.extend(["-d", args.dictionary])

        returncode = run_command(
            translate_cmd,
            f"Translating Markdown files ({args.source_lang} → {args.target_lang})"
        )

        if returncode != 0:
            print("\n✗ Pipeline failed at translation step")
            sys.exit(1)

        # Success!
        print("\n" + "=" * 80)
        print("✓ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"\nTranslated files are located in: {chunks_dir if not args.skip_chunking else project_dir}")
        print(f"Look for files ending with: _{args.target_lang}.md")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline cancelled by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
