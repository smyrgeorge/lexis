#!/usr/bin/env python3
"""
Markdown Translation Script

Translates markdown files using LLMs (Claude or ChatGPT).
Translated files are placed in the same directory as the source file by default.
Supports both single files and batch processing of directories.

Features:
- Automatically includes context from previous/next chunks to improve translation quality
- Skips already translated files when processing directories
- Supports custom dictionaries for specialized terminology

Usage:
# Translate a single file with Claude
python scripts/translate_md.py input.md -s Spanish -t English
# Translate all .md files in a directory (with context from adjacent chunks)
python scripts/translate_md.py ./markdown-dir -s Spanish -t English
# Disable context from adjacent chunks
python scripts/translate_md.py ./markdown-dir -s Spanish -t English -c 0
# Custom context lines (default is 5)
python scripts/translate_md.py ./markdown-dir -s Spanish -t English -c 10
# With OpenAI
python scripts/translate_md.py input.md -p openai -s Spanish -t English
# With dictionary
python scripts/translate_md.py input.md -s Spanish -t English -d dictionary.csv
# With custom output directory
python scripts/translate_md.py input.md -s Spanish -t English -o ./translations
"""

import argparse
import csv
import os
import re
import sys
import time
import warnings
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Suppress Pydantic V1 compatibility warning with Python 3.14+
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality.*", category=UserWarning)

default_openai_model = "gpt-4o"
default_claude_model = "claude-sonnet-4-5-20250929"
default_prompt = """
Translate the following markdown text from {source} to {target}.
Preserve all markdown formatting, structure, and syntax.
Only translate the text content, not the markdown syntax itself.
Only output the translated text, no additional text headings (e.g., "Translation:").
"""


def load_csv_dictionary(csv_path: str) -> str:
    """
    Load a CSV dictionary file and format it as a string.
    Expected CSV format: source_term,target_term

    Args:
        csv_path: Path to the CSV dictionary file

    Returns:
        Formatted string with the dictionary entries
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dictionary file not found: {csv_path}")

    dictionary_entries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        # Skip header if present
        header = next(reader, None)
        if header and header[0].lower() in ['source', 'term', 'original']:
            pass  # Header detected, already skipped
        else:
            # No header, process first row
            if header:
                dictionary_entries.append(f"{header[0]} -> {header[1]}")

        for row in reader:
            if len(row) >= 2:
                dictionary_entries.append(f"{row[0]} -> {row[1]}")

    if not dictionary_entries:
        return ""

    return "\n".join([
        "\n## Translation Dictionary",
        "Use the following term translations:",
        "```",
        *dictionary_entries,
        "```\n"
    ])


def translate_with_claude(
        text: str,
        prompt: str,
        dictionary: str,
        api_key: str,
        model: str = default_claude_model
) -> str:
    """Translate text using Claude API."""
    import anthropic
    from anthropic.types import MessageParam

    client = anthropic.Anthropic(api_key=api_key)
    full_prompt = f"{prompt}\n{dictionary}\n## Text to Translate:\n\n{text}"

    messages: list[MessageParam] = [
        {"role": "user", "content": full_prompt}
    ]

    message = client.messages.create(
        model=model,
        max_tokens=8000,
        messages=messages
    )

    text = message.content[0].text
    if not text or not text.strip():
        raise ValueError("API returned empty translation")
    return text


def translate_with_openai(
        text: str,
        prompt: str,
        dictionary: str,
        api_key: str,
        model: str = default_openai_model
) -> str:
    """Translate text using OpenAI API."""
    from openai import OpenAI
    from openai.types.chat import ChatCompletionUserMessageParam

    client = OpenAI(api_key=api_key)
    full_prompt = f"{prompt}\n{dictionary}\n## Text to Translate:\n\n{text}"

    messages: list[ChatCompletionUserMessageParam] = [
        {"role": "user", "content": full_prompt}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError("API returned empty translation")
    return content


def natural_sort_key(path: Path) -> list:
    """
    Generate a sort key for natural sorting of file names.
    This ensures that file10.md comes after file2.md, not before.

    Args:
        path: Path object to generate sort key for

    Returns:
        List of strings and integers for natural sorting
    """
    return [int(c) if c.isdigit() else c.lower()
            for c in re.split(r'(\d+)', str(path.name))]


def get_file_lines(file_path: str, num_lines: int, from_end: bool = False) -> list[str]:
    """
    Get the first or last N lines from a file.

    Args:
        file_path: Path to the file
        num_lines: Number of lines to get
        from_end: If True, get last N lines; if False, get first N lines

    Returns:
        List of lines
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if from_end:
                return lines[-num_lines:] if len(lines) >= num_lines else lines
            else:
                return lines[:num_lines] if len(lines) >= num_lines else lines
    except Exception as e:
        print(f"Warning: Could not read context from {file_path}: {e}")
        return []


# noinspection PyUnusedLocal
def translate_file(
        input_file: str,
        output_dir: str,
        provider: str,
        source_lang: str,
        target_lang: str,
        prompt: str,
        dictionary_path: Optional[str],
        model: Optional[str],
        prev_file: Optional[str] = None,
        next_file: Optional[str] = None,
        context_lines: int = 5
) -> None:
    """
    Translate a markdown file.

    Args:
        input_file: Path to input markdown file
        output_dir: Directory for output file
        provider: LLM provider ('claude' or 'openai')
        source_lang: Source language
        target_lang: Target language
        prompt: Translation prompt
        dictionary_path: Optional path to CSV dictionary
        model: Optional model override
        prev_file: Optional path to previous chunk file
        next_file: Optional path to next chunk file
        context_lines: Number of lines to include from prev/next chunks for context
    """
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Build context from previous and next chunks
    context_prefix = ""
    context_suffix = ""

    if prev_file and context_lines > 0:
        prev_lines = get_file_lines(prev_file, context_lines, from_end=True)
        if prev_lines:
            context_prefix = (
                "---\n"
                "## CONTEXT FROM PREVIOUS CHUNK (FOR REFERENCE ONLY - DO NOT TRANSLATE THIS SECTION)\n"
                "The following lines are from the previous chunk to provide context.\n"
                "DO NOT translate this section, only use it for context.\n"
                "---\n\n"
                + "".join(prev_lines) +
                "\n---\n"
                "## END OF PREVIOUS CHUNK CONTEXT\n"
                "---\n\n"
            )

    if next_file and context_lines > 0:
        next_lines = get_file_lines(next_file, context_lines, from_end=False)
        if next_lines:
            context_suffix = (
                "\n---\n"
                "## CONTEXT FROM NEXT CHUNK (FOR REFERENCE ONLY - DO NOT TRANSLATE THIS SECTION)\n"
                "The following lines are from the next chunk to provide context.\n"
                "DO NOT translate this section, only use it for context.\n"
                "---\n\n"
                + "".join(next_lines) +
                "\n---\n"
                "## END OF NEXT CHUNK CONTEXT\n"
                "---\n"
            )

    # Add main content marker if we have any context
    if context_prefix or context_suffix:
        content_with_context = (
            context_prefix +
            "---\n## MAIN CONTENT TO TRANSLATE\n"
            "Translate ONLY this section below:\n---\n\n" +
            content +
            "\n---\n## END OF MAIN CONTENT\n---\n" +
            context_suffix
        )
    else:
        content_with_context = content

    # Load dictionary if provided
    dictionary = ""
    if dictionary_path:
        dictionary = load_csv_dictionary(dictionary_path)

    # Get API key
    api_key_env = "ANTHROPIC_API_KEY" if provider == "claude" else "OPENAI_API_KEY"
    api_key = os.getenv(api_key_env)

    if not api_key:
        raise ValueError(f"{api_key_env} not found in environment variables")

    # Translate
    if context_prefix or context_suffix:
        print(f"Translating with {provider} (with context from adjacent chunks)...")
    else:
        print(f"Translating with {provider}...")
    start_time = time.time()

    if provider == "claude":
        translated = translate_with_claude(
            content_with_context,
            prompt,
            dictionary,
            api_key,
            model if model else default_claude_model
        )
    else:  # openai
        translated = translate_with_openai(
            content_with_context,
            prompt,
            dictionary,
            api_key,
            model if model else default_openai_model
        )

    elapsed_time = time.time() - start_time

    # Generate output filename
    input_path = Path(input_file)
    output_filename = f"{input_path.stem}_{target_lang}.md"
    output_path = Path(output_dir) / output_filename

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated)

    print(f"✓ Translation saved to: {output_path} (took {elapsed_time:.2f}s)")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Translate markdown files using LLMs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input_file",
        help="Path to input markdown file or directory containing markdown files"
    )

    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Output directory for translated files (default: same directory as input file)"
    )

    parser.add_argument(
        "-p", "--provider",
        choices=["claude", "openai"],
        default="claude",
        help="LLM provider to use"
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
        "--prompt",
        default=default_prompt,
        help="Translation prompt (use {source} and {target} as placeholders)"
    )

    parser.add_argument(
        "-d", "--dictionary",
        help="Path to CSV dictionary file (format: source_term,target_term)"
    )

    parser.add_argument(
        "-m", "--model",
        help="Model to use (overrides default)"
    )

    parser.add_argument(
        "-c", "--context-lines",
        type=int,
        default=5,
        help="Number of lines from previous/next chunks to include as context (default: 5, set to 0 to disable)"
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)

    # Check if input exists
    if not input_path.exists():
        print(f"Error: {args.input_file} does not exist")
        sys.exit(1)

    # Determine if input is a file or directory
    if input_path.is_file():
        # Single file mode
        files_to_process = [input_path]
    elif input_path.is_dir():
        # Directory mode - find all .md files
        all_md_files = sorted(input_path.glob("*.md"), key=natural_sort_key)
        if not all_md_files:
            print(f"Error: No .md files found in directory {args.input_file}")
            sys.exit(1)

        # Filter out already translated files (those ending with _{target_lang}.md)
        files_to_process = []
        skipped = 0
        for f in all_md_files:
            # Check if file ends with _{target_lang}.md
            if f.stem.endswith(f"_{args.target_lang}"):
                skipped += 1
                continue
            # Also skip if the translated version already exists
            translated_file = f.parent / f"{f.stem}_{args.target_lang}.md"
            if translated_file.exists():
                print(f"⊘ Skipping {f.name} (translation already exists)")
                skipped += 1
                continue
            files_to_process.append(f)

        if not files_to_process:
            print(f"No files to translate. All files are already translated or skipped.")
            sys.exit(0)

        print(
            f"Found {len(all_md_files)} markdown files ({skipped} already translated, {len(files_to_process)} to process)")
    else:
        print(f"Error: {args.input_file} is not a file or directory")
        sys.exit(1)

    # Format prompt with languages
    formatted_prompt = args.prompt.format(
        source=args.source_lang,
        target=args.target_lang
    )

    # Show cost estimation for batch processing
    if len(files_to_process) > 1:
        total_chars = 0
        for file_path in files_to_process:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_chars += len(f.read())
            except Exception:
                pass  # Skip files that can't be read

        est_tokens = total_chars // 4  # Rough estimate: 1 token ≈ 4 characters

        print(f"\n{'=' * 80}")
        print(f"📊 Batch Translation Estimate:")
        print(f"   Files to process: {len(files_to_process)}")
        print(f"   Total characters: {total_chars:,}")
        print(f"   Estimated input tokens: ~{est_tokens:,}")
        print(f"   Provider: {args.provider}")
        print(f"   Model: {args.model if args.model else (default_claude_model if args.provider == 'claude' else default_openai_model)}")
        print(f"\n   Note: Actual costs depend on output length and provider pricing.")
        print(f"   Context from adjacent chunks will add additional tokens.")
        print(f"{'=' * 80}")

    # Process files
    processed = 0
    failed = 0

    for idx, file_path in enumerate(files_to_process):
        # If no output directory specified, use the same directory as the input file
        output_dir = args.output_dir
        if output_dir is None:
            output_dir = str(file_path.parent)

        # Read current file for stats
        with open(file_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
            current_lines = current_content.split('\n')
            current_first_line = current_lines[0] if current_lines else ""
            current_char_count = len(current_content)

        # Determine previous and next files for context
        # Look at ALL files in the directory, not just files_to_process
        prev_file = None
        next_file = None
        prev_first_line = None
        next_first_line = None

        if args.context_lines > 0 and input_path.is_dir():
            # Get all .md files (including already translated ones) sorted
            all_source_files = sorted([
                f for f in input_path.glob("*.md")
                if not f.stem.endswith(f"_{args.target_lang}")
            ], key=natural_sort_key)

            # Find current file's position in the complete list
            try:
                current_idx = all_source_files.index(file_path)

                # Previous file (if not first)
                if current_idx > 0:
                    prev_file = str(all_source_files[current_idx - 1])
                    try:
                        with open(prev_file, 'r', encoding='utf-8') as f:
                            # Get the LAST non-empty line from previous chunk
                            lines = [line.strip() for line in f.readlines() if line.strip()]
                            prev_first_line = lines[-1] if lines else ""
                    except:
                        pass

                # Next file (if not last)
                if current_idx < len(all_source_files) - 1:
                    next_file = str(all_source_files[current_idx + 1])
                    try:
                        with open(next_file, 'r', encoding='utf-8') as f:
                            next_first_line = f.readline().strip()
                    except:
                        pass
            except ValueError:
                # File not found in list, skip context
                pass

        print(f"\n{'=' * 80}")
        print(f"[{idx + 1}/{len(files_to_process)}] Processing: {file_path.name}")
        print(f"  Characters: {current_char_count:,}")
        print(f"  First line: {current_first_line[:75]}{'...' if len(current_first_line) > 75 else ''}")
        if prev_file and args.context_lines > 0:
            print(f"\n  📄 Previous chunk: {Path(prev_file).name}")
            if prev_first_line:
                print(f"     Last line: {prev_first_line[:75]}{'...' if len(prev_first_line) > 75 else ''}")
        if next_file and args.context_lines > 0:
            print(f"\n  📄 Next chunk: {Path(next_file).name}")
            if next_first_line:
                print(f"     First line: {next_first_line[:75]}{'...' if len(next_first_line) > 75 else ''}")
        print(f"{'=' * 80}")

        try:
            translate_file(
                str(file_path),
                output_dir,
                args.provider,
                args.source_lang,
                args.target_lang,
                formatted_prompt,
                args.dictionary,
                args.model,
                prev_file,
                next_file,
                args.context_lines
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
        print(f"  Successfully translated: {processed}")
        print(f"  Failed: {failed}")
        print(f"{'=' * 80}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Translation cancelled by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
