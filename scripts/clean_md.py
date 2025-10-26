#!/usr/bin/env python3
"""
Markdown Cleaning Script

Cleans generated markdown files (from docling) by removing noise and keeping only meaningful content.
Uses facebook/bart-base model to refine the text while preserving markdown structure.

The cleaned file is saved in the same directory as the input file with a "_cleaned" suffix.

Usage:
# Clean a single markdown file
python scripts/clean_md.py input.md

# Clean a specific file with custom output directory
python scripts/clean_md.py input.md -o ./output

# Adjust the max tokens for generation (default: 512)
python scripts/clean_md.py input.md --max-tokens 1024

# Process in batch mode for multiple files
python scripts/clean_md.py ./markdown-dir

# Clean only translated files with specific suffix (e.g., _English.md)
python scripts/clean_md.py ./markdown-dir --suffix English

# Clean only files matching a pattern
python scripts/clean_md.py ./markdown-dir --suffix Spanish
"""

import argparse
import os
import sys
import time
from pathlib import Path

from transformers import pipeline


def refine_text(text: str, cleaner, max_tokens: int = 512) -> str:
    """
    Clean text using BART model and keep only meaningful content.

    Args:
        text: The text to clean
        cleaner: The transformers pipeline for text cleaning
        max_tokens: Maximum number of tokens to generate

    Returns:
        Cleaned text
    """
    prompt = f"Clean this text and keep only meaningful content:\n{text}"
    result = cleaner(prompt, max_new_tokens=max_tokens)[0]['generated_text']
    return result


def clean_file(
        input_file: str,
        output_dir: str,
        max_tokens: int,
        cleaner
) -> None:
    """
    Clean a markdown file.

    Args:
        input_file: Path to input markdown file
        output_dir: Directory for output file
        max_tokens: Maximum tokens for generation
        cleaner: The transformers pipeline for text cleaning
    """
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Cleaning with BART model...")
    print(f"  Input size: {len(content)} characters")
    start_time = time.time()

    # Clean the content
    cleaned_content = refine_text(content, cleaner, max_tokens)

    elapsed_time = time.time() - start_time

    # Generate output filename
    input_path = Path(input_file)
    output_filename = f"{input_path.stem}_cleaned.md"
    output_path = Path(output_dir) / output_filename

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    print(f"  Output size: {len(cleaned_content)} characters")
    print(f"✓ Cleaned file saved to: {output_path} (took {elapsed_time:.2f}s)")


def main():
    parser = argparse.ArgumentParser(
        description="Clean markdown files generated from docling",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input_file",
        help="Path to input markdown file or directory containing markdown files"
    )

    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Output directory for cleaned files (default: same directory as input file)"
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum number of tokens to generate"
    )

    parser.add_argument(
        "-s", "--suffix",
        default=None,
        help="Filter files by suffix pattern when processing directories (e.g., 'English' to match *_English.md)"
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)

    # Check if input exists
    if not input_path.exists():
        print(f"Error: {args.input_file} does not exist")
        sys.exit(1)

    # Initialize the BART model pipeline
    print("Loading BART model...")
    cleaner = pipeline("text2text-generation", model="facebook/bart-base")
    print("✓ Model loaded successfully")

    # Determine if input is a file or directory
    if input_path.is_file():
        # Single file mode
        files_to_process = [input_path]
    elif input_path.is_dir():
        # Directory mode - find all .md files
        all_md_files = sorted(input_path.glob("*.md"))
        if not all_md_files:
            print(f"Error: No .md files found in directory {args.input_file}")
            sys.exit(1)

        # Filter out already cleaned files and apply suffix filter if provided
        files_to_process = []
        skipped = 0
        filtered_by_suffix = 0

        for f in all_md_files:
            # Skip if file ends with _cleaned.md
            if f.stem.endswith("_cleaned"):
                skipped += 1
                continue

            # Apply suffix filter if provided
            if args.suffix:
                # Check if file matches the suffix pattern (e.g., _English.md)
                if not f.stem.endswith(f"_{args.suffix}"):
                    filtered_by_suffix += 1
                    continue

            # Also skip if the cleaned version already exists
            cleaned_file = f.parent / f"{f.stem}_cleaned.md"
            if cleaned_file.exists():
                print(f"⊘ Skipping {f.name} (cleaned version already exists)")
                skipped += 1
                continue

            files_to_process.append(f)

        if not files_to_process:
            if args.suffix:
                print(f"No files to clean. No files matching suffix '_{args.suffix}.md' found, or all are already cleaned.")
            else:
                print(f"No files to clean. All files are already cleaned or skipped.")
            sys.exit(0)

        status_msg = f"Found {len(all_md_files)} markdown files"
        if args.suffix:
            status_msg += f" ({filtered_by_suffix} filtered by suffix, {skipped} already cleaned, {len(files_to_process)} to process)"
        else:
            status_msg += f" ({skipped} already cleaned, {len(files_to_process)} to process)"
        print(status_msg)
    else:
        print(f"Error: {args.input_file} is not a file or directory")
        sys.exit(1)

    # Process files
    processed = 0
    failed = 0

    for file_path in files_to_process:
        # If no output directory specified, use the same directory as the input file
        output_dir = args.output_dir
        if output_dir is None:
            output_dir = str(file_path.parent)

        print(f"\n{'=' * 80}")
        print(f"Processing: {file_path.name}")
        print(f"{'=' * 80}")

        try:
            clean_file(
                str(file_path),
                output_dir,
                args.max_tokens,
                cleaner
            )
            processed += 1
        except Exception as e:
            print(f"✗ Error processing {file_path.name}: {e}")
            failed += 1

    # Summary
    if len(files_to_process) > 1:
        print(f"\n{'=' * 80}")
        print(f"Summary:")
        print(f"  Total files: {len(files_to_process)}")
        print(f"  Successfully cleaned: {processed}")
        print(f"  Failed: {failed}")
        print(f"{'=' * 80}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleaning cancelled by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
